from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from rest_framework import generics, status, serializers
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from accounts.models import TenantProfile, LandlordProfile
from accounts.permissions import IsLandlord
from leases.mpesa_utils import initiate_stk_push
from properties.models import Unit
from .models import *
from .serializers import *
from .services import *

# --- LEASE REQUEST VIEWS ---

class LeaseRequestCreateView(generics.CreateAPIView):
    serializer_class = LeaseRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        tenant = TenantProfile.objects.get(user=self.request.user)
        unit = Unit.objects.get(id=self.request.data.get("unit"))
        serializer.save(
            tenant=tenant,
            deposit_required=unit.deposit_amount,
            rent_required=unit.monthly_rent,
            required_amount=unit.deposit_amount + unit.monthly_rent,
            amount_paid=0,
            status="PAYMENT_PENDING"
        )

class MyLeaseRequestsView(generics.ListAPIView):
    serializer_class = LeaseRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LeaseRequest.objects.filter(tenant__user=self.request.user).order_by("-created_at")

class LandlordLeaseRequestListView(generics.ListAPIView):
    serializer_class = LeaseRequestSerializer
    permission_classes = [IsAuthenticated, IsLandlord]

    def get_queryset(self):
        return LeaseRequest.objects.filter(unit__property__landlord__user=self.request.user).order_by("-created_at")

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

        lease = Lease.objects.create(
            tenant=lr.tenant, unit=lr.unit, move_in_date=timezone.now().date(),
            entry_code=generate_entry_code(), deposit_held=lr.deposit_required, status="ACTIVE"
        )
        create_lease_wallet(lease)
        create_initial_rent_charge(lease, lr.rent_required)

        lr.status = "APPROVED"
        lr.save(update_fields=["status"])
        lr.unit.occupancy_status = "OCCUPIED"
        lr.unit.save(update_fields=["occupancy_status"])

        return Response({"message": "Lease approved successfully.", "lease_id": lease.id, "entry_code": lease.entry_code})

class RejectLeaseRequestView(generics.UpdateAPIView):
    serializer_class = LeaseRequestSerializer
    queryset = LeaseRequest.objects.all()
    permission_classes = [IsAuthenticated, IsLandlord]

    def update(self, request, *args, **kwargs):
        lr = self.get_object()
        lr.status = "REJECTED"
        lr.save(update_fields=["status"])
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
        return Response(res)

class InitiateLeaseWalletPaymentView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        tenant = TenantProfile.objects.get(user=request.user)
        amount = Decimal(request.data.get("amount"))
        phone = request.data.get("phone_number")
        lease = Lease.objects.get(id=request.data.get("lease"), tenant=tenant)

        pay = Payment.objects.create(tenant=tenant, lease=lease, amount=amount, phone_number=phone, status="PENDING")
        res = initiate_stk_push(phone_number=phone, amount=amount, account_reference=f"LEASE-{lease.id}")

        pay.checkout_request_id, pay.merchant_request_id = res.get("CheckoutRequestID", ""), res.get("MerchantRequestID", "")
        pay.save(update_fields=["checkout_request_id", "merchant_request_id"])
        return Response(res)

class MpesaCallbackView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        callback_data = request.data.get("Body", {}).get("stkCallback", {})
        payment = Payment.objects.filter(checkout_request_id=callback_data.get("CheckoutRequestID")).first()

        if not payment: return Response({"error": "Payment not found"}, status=404)
        if payment.status == "SUCCESS": return Response({"message": "Payment already processed"})

        if str(callback_data.get("ResultCode")) == "0":
            items = callback_data.get("CallbackMetadata", {}).get("Item", [])
            receipt = next((i.get("Value") for i in items if i.get("Name") == "MpesaReceiptNumber"), "")

            if payment.lease_request:
                payment.lease_request.amount_paid += payment.amount
                payment.lease_request.save(update_fields=["amount_paid"])

            if payment.lease:
                remaining = apply_payment_to_charges(payment.lease, payment.amount)
                if remaining > 0:
                    wallet = payment.lease.wallet
                    wallet.available_credit += remaining
                    wallet.save(update_fields=["available_credit"])

            payment.status, payment.mpesa_receipt = "SUCCESS", receipt
            payment.save(update_fields=["status", "mpesa_receipt"])
            return Response({"message": "Payment successful"})

        payment.status = "FAILED"
        payment.save(update_fields=["status"])
        return Response({"message": "Payment failed"})

class BillingCronView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if request.headers.get("X-BILLING-TOKEN") != settings.BILLING_CRON_TOKEN:
            return Response({"error": "Unauthorized"}, status=403)
        generate_due_rent_charges()
        return Response({"message": "Billing processed"})


# --- MOVE OUT VIEWS ---

class CreateMoveOutRequestView(generics.CreateAPIView):
    serializer_class = MoveOutRequestSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        lease = Lease.objects.filter(tenant__user=self.request.user, status="ACTIVE").first()
        if not lease: raise serializers.ValidationError("No active lease found.")
        if MoveOutRequest.objects.filter(lease=lease, status="PENDING").exists():
            raise serializers.ValidationError("You already have a pending move-out request.")
        serializer.save(lease=lease)

class MyMoveOutRequestsView(generics.ListAPIView):
    serializer_class = MoveOutRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return MoveOutRequest.objects.filter(lease__tenant__user=self.request.user)

class LandlordMoveOutRequestsView(generics.ListAPIView):
    serializer_class = MoveOutRequestSerializer
    permission_classes = [IsAuthenticated, IsLandlord]

    def get_queryset(self):
        return MoveOutRequest.objects.filter(lease__unit__property__landlord__user=self.request.user)

class ApproveMoveOutRequestView(generics.UpdateAPIView):
    queryset = MoveOutRequest.objects.all()
    permission_classes = [IsAuthenticated, IsLandlord]

    def update(self, request, *args, **kwargs):
        mo = self.get_object()
        if mo.status != "PENDING": return Response({"error": "Request already processed."}, 400)
        mo.status, mo.landlord_notes = "APPROVED", request.data.get("landlord_notes", "")
        mo.save(update_fields=["status", "landlord_notes"])
        return Response({"message": "Move-out approved."})

class RejectMoveOutRequestView(generics.UpdateAPIView):
    queryset = MoveOutRequest.objects.all()
    permission_classes = [IsAuthenticated, IsLandlord]

    def update(self, request, *args, **kwargs):
        mo = self.get_object()
        if mo.status != "PENDING": return Response({"error": "Request already processed."}, 400)
        mo.status, mo.landlord_notes = "REJECTED", request.data.get("landlord_notes", "")
        mo.save(update_fields=["status", "landlord_notes"])
        return Response({"message": "Move-out rejected."})

class CancelMoveOutRequestView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = MoveOutRequest.objects.all()

    def update(self, request, *args, **kwargs):
        mo = self.get_object()
        if mo.lease.tenant.user != request.user: return Response({"error": "You cannot cancel this request."}, status=403)
        if mo.status != "PENDING": return Response({"error": "Only pending requests can be cancelled."}, status=400)
        mo.status = "CANCELLED"
        mo.save(update_fields=["status"])
        return Response({"message": "Move-out request cancelled successfully."})