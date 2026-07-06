from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from django.db.models import Sum
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from accounts.models import TenantProfile, LandlordProfile
from accounts.permissions import IsLandlord
from properties.models import Unit
from .models import *
from .serializers import *
from .services import *
from .mpesa_utils import *

from .notifications import *


# ==========================================
# DRF CONTROLLERS / VIEWS
# ==========================================

# --- LEASE REQUEST VIEWS ---

class LeaseRequestCreateView(generics.CreateAPIView):
    serializer_class = LeaseRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        tenant = TenantProfile.objects.get(user=self.request.user)
        unit = Unit.objects.get(id=self.request.data.get("unit"))
        lr = serializer.save(
            tenant=tenant, deposit_required=unit.deposit_amount, rent_required=unit.monthly_rent,
            required_amount=unit.deposit_amount + unit.monthly_rent, amount_paid=0, status="PAYMENT_PENDING"
        )
        notify_lease_request_created(lr)

class MyLeaseRequestsView(generics.ListAPIView):
    serializer_class = LeaseRequestSerializer
    permission_classes = [IsAuthenticated]
    get_queryset = lambda self: LeaseRequest.objects.filter(tenant__user=self.request.user).order_by("-created_at")

class LandlordLeaseRequestListView(generics.ListAPIView):
    serializer_class = LeaseRequestSerializer
    permission_classes = [IsAuthenticated, IsLandlord]
    get_queryset = lambda self: LeaseRequest.objects.filter(unit__property__landlord__user=self.request.user).order_by("-created_at")

class ApproveLeaseRequestView(generics.UpdateAPIView):
    serializer_class = LeaseRequestSerializer
    permission_classes = [IsAuthenticated, IsLandlord]
    queryset = LeaseRequest.objects.all()

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        lr = self.get_object()
        if lr.status == "APPROVED": return Response({"error": "Lease request already approved."}, 400)
        if lr.status == "REJECTED": return Response({"error": "Cannot approve a rejected lease request."}, 400)
        if lr.amount_paid < lr.required_amount: return Response({"error": "Required payment not completed."}, 400)
        if lr.unit.occupancy_status == "OCCUPIED": return Response({"error": "This unit is already occupied."}, 400)
        if Lease.objects.filter(unit=lr.unit, status="ACTIVE").exists(): return Response({"error": "Active lease exists."}, 400)

        lease = Lease.objects.create(tenant=lr.tenant, unit=lr.unit, move_in_date=timezone.now().date(), entry_code=generate_entry_code(), deposit_held=lr.deposit_required, status="ACTIVE")
        create_lease_wallet(lease)
        create_initial_rent_charge(lease, lr.rent_required)

        lr.status, lr.unit.occupancy_status = "APPROVED", "OCCUPIED"
        lr.save(update_fields=["status"]), lr.unit.save(update_fields=["occupancy_status"])
        
        notify_lease_approved(lease)
        return Response({"message": "Lease approved successfully.", "lease_id": lease.id, "entry_code": lease.entry_code})

class RejectLeaseRequestView(generics.UpdateAPIView):
    serializer_class = LeaseRequestSerializer
    queryset = LeaseRequest.objects.all()
    permission_classes = [IsAuthenticated, IsLandlord]

    def update(self, request, *args, **kwargs):
        lr = self.get_object()
        lr.status = "REJECTED"
        lr.save(update_fields=["status"])
        notify_lease_rejected(lr)
        return Response({"message": "Lease request rejected"})


# --- MPESA & BILLING VIEWS ---

class InitiateLeaseRequestPaymentView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        tenant = TenantProfile.objects.get(user=request.user)
        phone = request.data.get("phone_number")
        lr = LeaseRequest.objects.get(id=request.data.get("lease_request"), tenant=tenant)

        if lr.amount_paid >= lr.required_amount: return Response({"error": "Already fully paid."}, 400)
        if lr.status == "APPROVED": return Response({"error": "Already approved."}, 400)

        amount = lr.required_amount - lr.amount_paid
        pay = Payment.objects.create(tenant=tenant, lease_request=lr, amount=amount, phone_number=phone, status="PENDING")
        res = initiate_stk_push(phone_number=phone, amount=amount, account_reference=f"LR-{lr.id}")

        pay.checkout_request_id, pay.merchant_request_id = res.get("CheckoutRequestID", ""), res.get("MerchantRequestID", "")
        pay.save(update_fields=["checkout_request_id", "merchant_request_id"])
        
        notify_stk_sent(pay)
        return Response(res)

class InitiateLeaseWalletPaymentView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        tenant = TenantProfile.objects.get(user=request.user)
        amount, phone = Decimal(request.data.get("amount")), request.data.get("phone_number")
        lease = Lease.objects.get(id=request.data.get("lease"), tenant=tenant)

        pay = Payment.objects.create(tenant=tenant, lease=lease, amount=amount, phone_number=phone, status="PENDING")
        res = initiate_stk_push(phone_number=phone, amount=amount, account_reference=f"LEASE-{lease.id}")

        pay.checkout_request_id, pay.merchant_request_id = res.get("CheckoutRequestID", ""), res.get("MerchantRequestID", "")
        pay.save(update_fields=["checkout_request_id", "merchant_request_id"])
        
        notify_stk_sent(pay)
        return Response(res)

class MpesaCallbackView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        cb = request.data.get("Body", {}).get("stkCallback", {})
        checkout_id = cb.get("CheckoutRequestID")
        res_code = str(cb.get("ResultCode", ""))

        if not checkout_id:
            return Response({"error": "Invalid callback structure"}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Look up the incoming payload reference against both transaction variants
        payment = Payment.objects.filter(checkout_request_id=checkout_id).first()
        st_tx = SettlementTransaction.objects.filter(checkout_request_id=checkout_id).first()
        
        if not payment and not st_tx: 
            return Response({"error": "Transaction not found"}, status=status.HTTP_404_NOT_FOUND)

        # 2. Handle transaction failures gracefully (Safaricom ResultCode != "0")
        if res_code != "0":
            if payment: 
                payment.status = "FAILED"
                payment.save(update_fields=["status"])
                notify_stk_failed(payment)
                
            if st_tx: 
                st_tx.status = "FAILED"
                st_tx.save(update_fields=["status"])
                # 👇 Using your explicit settlement-specific failure tracker hook
                notify_settlement_stk_failed(st_tx)
                
            return Response({"message": "Payment recorded as failed."})

        # 3. Extract Safaricom's alphanumeric tracking code
        receipt = next(
            (i.get("Value") for i in cb.get("CallbackMetadata", {}).get("Item", []) if i.get("Name") == "MpesaReceiptNumber"), 
            ""
        )

        # 4. PROCESS VARIANT A: Standard Lease / Wallet Top-Up Payment Flow
        if payment:
            if payment.status == "SUCCESS": 
                return Response({"message": "Payment already processed"})
            
            # Wrap business calculations in an atomic transaction lock for data integrity
            with transaction.atomic():
                if payment.lease_request:
                    payment.lease_request.amount_paid += payment.amount
                    payment.lease_request.save(update_fields=["amount_paid"])
                elif payment.lease:
                    rem = apply_payment_to_charges(payment.lease, payment.amount)
                    if rem > 0:
                        payment.lease.wallet.available_credit += rem
                        payment.lease.wallet.save(update_fields=["available_credit"])
                
                payment.status, payment.mpesa_receipt = "SUCCESS", receipt
                payment.save(update_fields=["status", "mpesa_receipt"])
            
            # Re-fetch structural relational dependencies before dispatching alerts
            payment.refresh_from_db(fields=['lease_request', 'lease', 'tenant'])
            
            notify_payment_success(payment)
            return Response({"message": "Payment processed successfully."})

        # 5. PROCESS VARIANT B: Lease Move-Out Closing Settlement Sheet Balance Flow
        if st_tx:
            if st_tx.status == "SUCCESS": 
                return Response({"message": "Settlement already processed"})
            
            with transaction.atomic():
                st_tx.status, st_tx.mpesa_receipt = "SUCCESS", receipt
                st_tx.save(update_fields=["status", "mpesa_receipt"])
                reconcile_settlement(st_tx.settlement)
            
            # Real-time alert explicitly for settlement balance closure collections
            notify_settlement_payment_received(st_tx.settlement)
            return Response({"message": "Settlement payment recorded successfully."})

class BillingCronView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if request.headers.get("X-BILLING-TOKEN") != settings.BILLING_CRON_TOKEN: return Response({"error": "Unauthorized"}, 403)
        generate_due_rent_charges()
        return Response({"message": "Billing processed"})


# --- MOVE OUT VIEWS ---

class CreateMoveOutRequestView(generics.CreateAPIView):
    serializer_class = MoveOutRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        try:
            lease = Lease.objects.get(id=self.request.data.get("lease"), tenant__user=self.request.user, status="ACTIVE")
        except Lease.DoesNotExist:
            raise serializers.ValidationError("Active lease not found.")

        if MoveOutRequest.objects.filter(lease=lease, status="PENDING").exists():
            raise serializers.ValidationError("You already have a pending move-out request.")
        mo = serializer.save(lease=lease)
        notify_move_out_request(mo)

class MyMoveOutRequestsView(generics.ListAPIView):
    serializer_class = MoveOutRequestSerializer
    permission_classes = [IsAuthenticated]
    get_queryset = lambda self: MoveOutRequest.objects.filter(lease__tenant__user=self.request.user)

class LandlordMoveOutRequestsView(generics.ListAPIView):
    serializer_class = MoveOutRequestSerializer
    permission_classes = [IsAuthenticated, IsLandlord]
    get_queryset = lambda self: MoveOutRequest.objects.filter(lease__unit__property__landlord__user=self.request.user)

class ApproveMoveOutRequestView(generics.UpdateAPIView):
    # 👇 Use select_related to pre-fetch the lease, tenant, user, and unit database records
    queryset = MoveOutRequest.objects.all().select_related(
        'lease__tenant__user', 
        'lease__unit'
    )
    permission_classes = [IsAuthenticated, IsLandlord]

    def update(self, request, *args, **kwargs):
        mo = self.get_object()
        if mo.status != "PENDING": 
            return Response({"error": "Request already processed."}, 400)
            
        mo.status, mo.landlord_notes = "APPROVED", request.data.get("landlord_notes", "")
        mo.save(update_fields=["status", "landlord_notes"])
        
        # Call the notification function safely
        notify_move_out_approved(mo)
        
        return Response({"message": "Move-out approved."})

class RejectMoveOutRequestView(generics.UpdateAPIView):
    queryset = MoveOutRequest.objects.all()
    permission_classes = [IsAuthenticated, IsLandlord]

    def update(self, request, *args, **kwargs):
        mo = self.get_object()
        if mo.status != "PENDING": return Response({"error": "Request already processed."}, 400)
        mo.status, mo.landlord_notes = "REJECTED", request.data.get("landlord_notes", "")
        mo.save(update_fields=["status", "landlord_notes"])
        notify_move_out_rejected(mo)
        return Response({"message": "Move-out rejected."})

class CancelMoveOutRequestView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = MoveOutRequest.objects.all()

    def update(self, request, *args, **kwargs):
        mo = self.get_object()
        if mo.lease.tenant.user != request.user: return Response({"error": "You cannot cancel this request."}, 403)
        if mo.status != "PENDING": return Response({"error": "Only pending requests can be cancelled."}, 400)
        mo.status = "CANCELLED"
        mo.save(update_fields=["status"])
        return Response({"message": "Move-out request cancelled successfully."})

class CreateInspectionView(generics.CreateAPIView):
    serializer_class = PropertyInspectionSerializer
    permission_classes = [IsAuthenticated, IsLandlord]

    def perform_create(self, serializer):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        move_out = MoveOutRequest.objects.get(id=self.request.data.get("move_out_request"))
        if move_out.status != "APPROVED": raise serializers.ValidationError("Move-out request must be approved.")
        if hasattr(move_out, "inspection"): raise serializers.ValidationError("Inspection already exists.")
        serializer.save(inspected_by=landlord, move_out_request=move_out)

class CreateInspectionItemView(generics.CreateAPIView):
    serializer_class = InspectionItemSerializer
    permission_classes = [IsAuthenticated, IsLandlord]

    def perform_create(self, serializer):
        inspection = PropertyInspection.objects.get(id=self.request.data.get("inspection"))
        if inspection.status == "COMPLETED": raise serializers.ValidationError("Inspection already completed.")
        serializer.save(inspection=inspection)

class InspectionDetailView(generics.RetrieveAPIView):
    queryset = PropertyInspection.objects.all()
    serializer_class = PropertyInspectionSerializer
    permission_classes = [IsAuthenticated]

class CompleteInspectionView(generics.UpdateAPIView):
    queryset = PropertyInspection.objects.all()
    permission_classes = [IsAuthenticated, IsLandlord]

    def update(self, request, *args, **kwargs):
        inspection = self.get_object()
        inspection.status, inspection.general_notes = "COMPLETED", request.data.get("general_notes", "")
        inspection.save(update_fields=["status", "general_notes"])
        s = create_settlement(inspection)
        
        notify_inspection_completed(inspection, s)
        return Response({
            "message": "Inspection completed successfully.",
            "settlement": {
                "deposit_amount": s.deposit_amount, "wallet_credit": s.wallet_credit, "outstanding_rent": s.outstanding_rent,
                "damage_cost": s.damage_cost, "refund_amount": s.refund_amount, "amount_owed": s.amount_owed, "status": s.status,
            }
        })


# --- SETTLEMENT & FINALIZE VIEWS ---

class RecordSettlementPaymentView(generics.UpdateAPIView):
    queryset = LeaseSettlement.objects.all()
    permission_classes = [IsAuthenticated, IsLandlord]

    def update(self, request, *args, **kwargs):
        settlement = self.get_object()
        p_type = request.data.get("payment_type")
        now = timezone.now()

        if p_type == "PAYMENT":
            settlement.balance_received = True
            settlement.balance_received_at = now
        elif p_type == "SETTLEMENT":
            settlement.refund_paid = True
            settlement.refund_paid_at = now
        else:
            return Response({"error": "Invalid payment type. Must be 'PAYMENT' or 'SETTLEMENT'."}, 400)

        settlement.payment_notes = request.data.get("payment_notes", "")
        settlement.save(update_fields=["refund_paid", "refund_paid_at", "balance_received", "balance_received_at", "payment_notes"])
        
        notify_settlement_ledger_updated(settlement, p_type)
        return Response({"message": f"Settlement transaction recorded under {p_type} successfully."})

class FinalizeMoveOutView(generics.UpdateAPIView):
    queryset = LeaseSettlement.objects.all()
    permission_classes = [IsAuthenticated, IsLandlord]

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        settlement = self.get_object()

        if settlement.status == "FINALIZED":
            return Response({"error": "Settlement already finalized."}, status=status.HTTP_400_BAD_REQUEST)
        
        if settlement.refund_amount > 0 and not settlement.refund_paid:
            return Response({"error": "The settlement payout has not yet been recorded as paid."}, status=status.HTTP_400_BAD_REQUEST)
        if settlement.amount_owed > 0 and not settlement.balance_received:
            return Response({"error": "The incoming clearance payment has not yet been recorded as received."}, status=status.HTTP_400_BAD_REQUEST)

        now = timezone.now()
        move_out = settlement.inspection.move_out_request
        lease, unit = move_out.lease, move_out.lease.unit

        settlement.status = "FINALIZED"
        settlement.save(update_fields=["status"])

        lease.status, lease.move_out_date, lease.entry_code = "COMPLETED", now.date(), None
        lease.save(update_fields=["status", "move_out_date", "entry_code"])

        unit.occupancy_status = "AVAILABLE"
        unit.save(update_fields=["occupancy_status"])

        move_out.completed_at = now
        move_out.save(update_fields=["completed_at"])

        notify_lease_finalized(settlement)
        return Response({
            "message": "Move-out finalized successfully.",
            "settlement": {k: getattr(settlement, k) for k in ["id", "status", "refund_amount", "refund_paid", "amount_owed", "balance_received"]},
            "lease": {k: getattr(lease, k) for k in ["id", "status", "move_out_date", "entry_code"]},
            "unit": {"id": unit.id, "occupancy_status": unit.occupancy_status},
            "move_out_completed_at": move_out.completed_at,
        }, status=status.HTTP_200_OK)

class InitiateSettlementPaymentView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # 1. Safely grab tenant profile
        tenant = TenantProfile.objects.filter(user=request.user).first()
        if not tenant:
            return Response(
                {"error": "Access denied. A valid Tenant Profile is required."},
                status=status.HTTP_403_FORBIDDEN
            )

        settlement_id = request.data.get("settlement")
        if not settlement_id:
            return Response({"error": "Settlement ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Safely grab settlement record
        try:
            settlement = LeaseSettlement.objects.get(
                id=settlement_id, 
                inspection__move_out_request__lease__tenant=tenant
            )
        except LeaseSettlement.DoesNotExist:
            return Response(
                {"error": "Settlement record not found or unauthorized access."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Status guards
        if settlement.status == "FINANCIALLY_SETTLED": 
            return Response({"error": "Settlement is already fully settled."}, status=status.HTTP_400_BAD_REQUEST)
            
        if settlement.amount_owed <= 0: 
            return Response({"error": "Nothing to pay for this settlement."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Check balance remaining
        successful_payments = SettlementTransaction.objects.filter(
            settlement=settlement, 
            transaction_type="COLLECTION", 
            status="SUCCESS"
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
        
        remaining = settlement.amount_owed - successful_payments
        if remaining <= 0:
            reconcile_settlement(settlement)
            return Response({"message": "Settlement already fully paid."})

        # 5. Check phone input
        phone = request.data.get("phone_number")
        if not phone:
            return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 6. Create the pending ledger transaction tracking row
        tx = SettlementTransaction.objects.create(
            settlement=settlement, 
            transaction_type="COLLECTION", 
            payment_method="MPESA_STK", 
            amount=remaining, 
            phone_number=phone, 
            status="PENDING"
        )
        
        # 7. Execute external Daraja API Push Request
        try:
            res = initiate_stk_push(
                phone_number=phone, 
                amount=remaining, 
                account_reference=f"SETTLEMENT-{settlement.id}"
            )
            
            # Save Safaricom tracking references
            tx.checkout_request_id = res.get("CheckoutRequestID", "")
            tx.merchant_request_id = res.get("MerchantRequestID", "")
            tx.save(update_fields=["checkout_request_id", "merchant_request_id"])
            
            # 🚨 FIXED: Call the correct, isolated settlement function explicitly
            notify_settlement_stk_sent(tx)
            
            return Response(res, status=status.HTTP_200_OK)
            
        except Exception as stk_err:
            tx.status = "FAILED"
            tx.save(update_fields=["status"])
            return Response(
                {"error": f"Failed to connect to M-Pesa Gateway: {str(stk_err)}"}, 
                status=status.HTTP_502_BAD_GATEWAY
            )

class InitiateSettlementPaymentView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        # 1. Safely locate the tenant's profile without throwing a 500 server crash
        tenant = TenantProfile.objects.filter(user=request.user).first()
        if not tenant:
            return Response(
                {"error": "Access denied. A valid Tenant Profile is required to initiate settlement payments."},
                status=status.HTTP_403_FORBIDDEN
            )

        settlement_id = request.data.get("settlement")
        if not settlement_id:
            return Response({"error": "Settlement ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        # 2. Safely locate the specific settlement record
        try:
            settlement = LeaseSettlement.objects.get(
                id=settlement_id, 
                inspection__move_out_request__lease__tenant=tenant
            )
        except LeaseSettlement.DoesNotExist:
            return Response(
                {"error": "Settlement record not found or unauthorized access."}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # 3. Check baseline payment constraints
        if settlement.status == "FINANCIALLY_SETTLED": 
            return Response({"error": "Settlement is already fully settled."}, status=status.HTTP_400_BAD_REQUEST)
            
        if settlement.amount_owed <= 0: 
            return Response({"error": "Nothing to pay for this settlement sheet."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Aggregate successful payments to determine the true remaining balance
        successful_payments = SettlementTransaction.objects.filter(
            settlement=settlement, 
            transaction_type="COLLECTION", 
            status="SUCCESS"
        ).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")
        
        remaining = settlement.amount_owed - successful_payments
        if remaining <= 0:
            reconcile_settlement(settlement)
            return Response({"message": "Settlement already fully paid."})

        # 5. Handle M-Pesa Phone Number input verification
        phone = request.data.get("phone_number")
        if not phone:
            return Response({"error": "Phone number is required to process M-Pesa payments."}, status=status.HTTP_400_BAD_REQUEST)

        # 6. Initialize local tracking row
        tx = SettlementTransaction.objects.create(
            settlement=settlement, 
            transaction_type="COLLECTION", 
            payment_method="MPESA_STK", 
            amount=remaining, 
            phone_number=phone, 
            status="PENDING"
        )
        
        # 7. Safe Execution Block for external M-Pesa/Daraja push requests
        try:
            res = initiate_stk_push(
                phone_number=phone, 
                amount=remaining, 
                account_reference=f"SETTLEMENT-{settlement.id}"
            )
            
            # Map tracking references returned from Daraja API
            tx.checkout_request_id = res.get("CheckoutRequestID", "")
            tx.merchant_request_id = res.get("MerchantRequestID", "")
            tx.save(update_fields=["checkout_request_id", "merchant_request_id"])
            
            # Fire off push alerts/emails confirming prompt departure
            notify_settlement_stk_sent(tx)
            return Response(res, status=status.HTTP_200_OK)
            
        except Exception as stk_err:
            # Drop tracking row status if integration gateway drops or errors
            tx.status = "FAILED"
            tx.save(update_fields=["status"])
            return Response(
                {"error": f"Failed to connect to M-Pesa Gateway: {str(stk_err)}"}, 
                status=status.HTTP_502_BAD_GATEWAY
            )
class B2CQueueTimeoutView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        tx = SettlementTransaction.objects.filter(conversation_id=request.data.get("ConversationID", "")).first()
        if tx:
            tx.status, tx.result_desc = "FAILED", "Queue timeout."
            tx.save(update_fields=["status", "result_desc"])
        return Response({"message": "Timeout received."}, status=200)

class B2CResultCallbackView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        res = request.data.get("Result", {})
        tx = SettlementTransaction.objects.filter(conversation_id=res.get("ConversationID")).select_related("settlement").first()

        if not tx:
            return Response({"error": "Transaction not found."}, status=status.HTTP_404_NOT_FOUND)

        if tx.status == "SUCCESS":
            return Response({"message": "Refund already processed."}, status=status.HTTP_200_OK)

        tx.result_code = str(res.get("ResultCode", ""))
        tx.result_desc = res.get("ResultDesc", "")

        simulate_success = (settings.SIMULATE_B2C_SUCCESS and tx.result_desc == "The security credential is locked.")

        if tx.result_code == "0" or simulate_success:
            tx.status = "SUCCESS"
            tx.save(update_fields=["status", "result_code", "result_desc"])

            settlement = tx.settlement
            settlement.refund_paid = True
            settlement.refund_paid_at = timezone.now()
            settlement.save(update_fields=["refund_paid", "refund_paid_at"])

            reconcile_settlement(settlement)
            
            notify_settlement_ledger_updated(settlement, "SETTLEMENT")
            return Response({"message": "Refund completed successfully.", "simulated": simulate_success, "settlement_status": settlement.status}, status=status.HTTP_200_OK)

        tx.status = "FAILED"
        tx.save(update_fields=["status", "result_code", "result_desc"])
        return Response({"message": "Refund failed.", "reason": tx.result_desc, "result_code": tx.result_code}, status=status.HTTP_200_OK)