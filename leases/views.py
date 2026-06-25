from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from rest_framework import generics, status
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
        return LeaseRequest.objects.filter(tenant=TenantProfile.objects.get(user=self.request.user)).order_by("-created_at")

class LandlordLeaseRequestListView(generics.ListAPIView):
    serializer_class = LeaseRequestSerializer
    permission_classes = [IsAuthenticated, IsLandlord]

    def get_queryset(self):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        return LeaseRequest.objects.filter(unit__property__landlord=landlord).order_by("-created_at")

class ApproveLeaseRequestView(generics.UpdateAPIView):
    serializer_class = LeaseRequestSerializer
    permission_classes = [IsAuthenticated, IsLandlord]
    queryset = LeaseRequest.objects.all()

    @transaction.atomic
    def update(self, request, *args, **kwargs):
        lease_request = self.get_object()

        if lease_request.status == "APPROVED":
            return Response({"error": "Lease request already approved."}, status=400)
        if lease_request.status == "REJECTED":
            return Response({"error": "Cannot approve a rejected lease request."}, status=400)
        if lease_request.amount_paid < lease_request.required_amount:
            return Response({"error": "Required payment not completed."}, status=400)
        if lease_request.unit.occupancy_status == "OCCUPIED":
            return Response({"error": "This unit is already occupied."}, status=400)
        if Lease.objects.filter(unit=lease_request.unit, status="ACTIVE").exists():
            return Response({"error": "An active lease already exists for this unit."}, status=400)

        lease = Lease.objects.create(
            tenant=lease_request.tenant,
            unit=lease_request.unit,
            move_in_date=timezone.now().date(),
            entry_code=generate_entry_code(),
            deposit_held=lease_request.deposit_required,
            status="ACTIVE"
        )
        create_lease_wallet(lease)
        create_initial_rent_charge(lease, lease_request.rent_required)

        lease_request.status = "APPROVED"
        lease_request.save()

        lease_request.unit.occupancy_status = "OCCUPIED"
        lease_request.unit.save()

        return Response({"message": "Lease approved successfully.", "lease_id": lease.id, "entry_code": lease.entry_code})

class RejectLeaseRequestView(generics.UpdateAPIView):
    serializer_class = LeaseRequestSerializer
    queryset = LeaseRequest.objects.all()
    permission_classes = [IsAuthenticated, IsLandlord]

    def update(self, request, *args, **kwargs):
        lease_request = self.get_object()
        lease_request.status = "REJECTED"
        lease_request.save()
        return Response({"message": "Lease request rejected"})

class InitiateLeaseRequestPaymentView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        tenant = TenantProfile.objects.get(user=request.user)
        phone = request.data.get("phone_number")
        lease_request = LeaseRequest.objects.get(id=request.data.get("lease_request"), tenant=tenant)

        if lease_request.amount_paid >= lease_request.required_amount:
            return Response({"error": "This lease request is already fully paid."}, status=400)
        if lease_request.status == "APPROVED":
            return Response({"error": "This lease request has already been approved."}, status=400)

        amount = lease_request.required_amount - lease_request.amount_paid
        payment = Payment.objects.create(tenant=tenant, lease_request=lease_request, amount=amount, phone_number=phone, status="PENDING")
        result = initiate_stk_push(phone_number=phone, amount=amount, account_reference=f"LR-{lease_request.id}")

        payment.checkout_request_id = result.get("CheckoutRequestID", "")
        payment.merchant_request_id = result.get("MerchantRequestID", "")
        payment.save()
        return Response(result)

class InitiateLeaseWalletPaymentView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        tenant = TenantProfile.objects.get(user=request.user)
        amount = Decimal(request.data.get("amount"))
        phone = request.data.get("phone_number")
        lease = Lease.objects.get(id=request.data.get("lease"), tenant=tenant)

        payment = Payment.objects.create(tenant=tenant, lease=lease, amount=amount, phone_number=phone, status="PENDING")
        result = initiate_stk_push(phone_number=phone, amount=amount, account_reference=f"LEASE-{lease.id}")

        payment.checkout_request_id = result.get("CheckoutRequestID", "")
        payment.merchant_request_id = result.get("MerchantRequestID", "")
        payment.save()
        return Response(result)

class MpesaCallbackView(generics.CreateAPIView):
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):

        callback_data = request.data.get("Body", {}).get("stkCallback", {})

        checkout_id = callback_data.get("CheckoutRequestID")
        result_code = callback_data.get("ResultCode")

        payment = Payment.objects.filter(
            checkout_request_id=checkout_id
        ).first()

        if not payment:
            return Response(
                {"error": "Payment not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Prevent duplicate callback processing
        if payment.status == "SUCCESS":
            return Response(
                {"message": "Payment already processed"},
                status=status.HTTP_200_OK
            )

        # Successful payment
        if str(result_code) == "0":

            items = callback_data.get(
                "CallbackMetadata",
                {}
            ).get(
                "Item",
                []
            )

            receipt_number = next(
                (
                    item.get("Value")
                    for item in items
                    if item.get("Name") == "MpesaReceiptNumber"
                ),
                ""
            )

            # Lease request payment
            if payment.lease_request:

                payment.lease_request.amount_paid += payment.amount
                payment.lease_request.save()

            # Existing tenant lease payment
            if payment.lease:

                remaining = apply_payment_to_charges(
                    payment.lease,
                    payment.amount
                )

                # Anything left goes into wallet
                if remaining > 0:

                    wallet = payment.lease.wallet
                    wallet.available_credit += remaining
                    wallet.save()

            payment.status = "SUCCESS"
            payment.mpesa_receipt = receipt_number
            payment.save()

            return Response(
                {"message": "Payment successful"},
                status=status.HTTP_200_OK
            )

        # Failed payment
        payment.status = "FAILED"
        payment.save()

        return Response(
            {"message": "Payment failed"},
            status=status.HTTP_200_OK
        )


class BillingCronView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):

        token = request.headers.get("X-BILLING-TOKEN")

        if token != settings.BILLING_CRON_TOKEN:
            return Response(
                {"error": "Unauthorized"},
                status=403
            )

        generate_due_rent_charges()

        return Response(
            {"message": "Billing processed"}
        )