from django.utils import timezone
from decimal import Decimal

from rest_framework import generics
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.models import (
    TenantProfile,
    LandlordProfile
)

from accounts.permissions import IsLandlord
from leases.mpesa_utils import initiate_stk_push
from properties.models import Unit

from .models import *
from .serializers import *
from .services import *

class LeaseRequestCreateView(
    generics.CreateAPIView
):

    serializer_class = (
        LeaseRequestSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def perform_create(
        self,
        serializer
    ):

        tenant = (
            TenantProfile.objects.get(
                user=self.request.user
            )
        )

        unit_id = self.request.data.get(
            "unit"
        )

        unit = Unit.objects.get(
            id=unit_id
        )

        serializer.save(
            tenant=tenant,
            required_amount=unit.monthly_rent,
            amount_paid=0,
            status="PAYMENT_PENDING"
        )

class MyLeaseRequestsView(
    generics.ListAPIView
):

    serializer_class = (
        LeaseRequestSerializer
    )

    permission_classes = [
        IsAuthenticated
    ]

    def get_queryset(self):

        tenant = (
            TenantProfile.objects.get(
                user=self.request.user
            )
        )

        return LeaseRequest.objects.filter(
            tenant=tenant
        ).order_by(
            "-created_at"
        )
    
class LandlordLeaseRequestListView(
    generics.ListAPIView
):

    serializer_class = (
        LeaseRequestSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsLandlord
    ]

    def get_queryset(self):

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        return LeaseRequest.objects.filter(
            unit__property__landlord=landlord
        ).order_by(
            "-created_at"
        )
    
class ApproveLeaseRequestView(
    generics.UpdateAPIView
):

    serializer_class = (
        LeaseRequestSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsLandlord
    ]

    queryset = LeaseRequest.objects.all()

    def update(
        self,
        request,
        *args,
        **kwargs
    ):

        lease_request = self.get_object()

        if lease_request.amount_paid < lease_request.required_amount:

            return Response(
                {
                    "error":
                    "Required payment not completed."
                },
                status=400
            )

        lease_request.status = (
            "APPROVED"
        )

        lease_request.save()

        lease = Lease.objects.create(
            tenant=lease_request.tenant,
            unit=lease_request.unit,
            move_in_date=timezone.now().date(),
            entry_code=generate_entry_code()
        )

        create_lease_wallet(
            lease
        )

        lease_request.unit.occupancy_status = (
            "OCCUPIED"
        )

        lease_request.unit.save()

        return Response(
            {
                "message":
                "Lease approved",

                "entry_code":
                lease.entry_code
            }
        )
    
class RejectLeaseRequestView(
    generics.UpdateAPIView
):

    serializer_class = (
        LeaseRequestSerializer
    )

    queryset = LeaseRequest.objects.all()

    permission_classes = [
        IsAuthenticated,
        IsLandlord
    ]

    def update(
        self,
        request,
        *args,
        **kwargs
    ):

        lease_request = self.get_object()

        lease_request.status = (
            "REJECTED"
        )

        lease_request.save()

        return Response(
            {
                "message":
                "Lease request rejected"
            }
        )
    
class InitiateLeaseRequestPaymentView(
    generics.CreateAPIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        tenant = (
            TenantProfile.objects.get(
                user=request.user
            )
        )

        lease_request_id = (
            request.data.get(
                "lease_request"
            )
        )

        phone = request.data.get(
            "phone_number"
        )

        lease_request = (
            LeaseRequest.objects.get(
                id=lease_request_id,
                tenant=tenant
            )
        )

        amount = (
            lease_request.required_amount
            -
            lease_request.amount_paid
        )

        payment = Payment.objects.create(
            tenant=tenant,
            lease_request=lease_request,
            amount=amount,
            phone_number=phone,
            status="PENDING"
        )

        result = initiate_stk_push(
            phone_number=phone,
            amount=amount,
            account_reference=
            f"LR-{lease_request.id}"
        )

        payment.checkout_request_id = (
            result.get(
                "CheckoutRequestID",
                ""
            )
        )

        payment.merchant_request_id = (
            result.get(
                "MerchantRequestID",
                ""
            )
        )

        payment.save()

        return Response(result)
    
class InitiateLeaseWalletPaymentView(
    generics.CreateAPIView
):

    permission_classes = [
        IsAuthenticated
    ]

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        tenant = (
            TenantProfile.objects.get(
                user=request.user
            )
        )

        lease_id = request.data.get(
            "lease"
        )

        amount = Decimal(
            request.data.get(
                "amount"
            )
        )

        phone = request.data.get(
            "phone_number"
        )

        lease = Lease.objects.get(
            id=lease_id,
            tenant=tenant
        )

        payment = Payment.objects.create(
            tenant=tenant,
            lease=lease,
            amount=amount,
            phone_number=phone,
            status="PENDING"
        )

        result = initiate_stk_push(
            phone_number=phone,
            amount=amount,
            account_reference=
            f"LEASE-{lease.id}"
        )

        payment.checkout_request_id = (
            result.get(
                "CheckoutRequestID",
                ""
            )
        )

        payment.merchant_request_id = (
            result.get(
                "MerchantRequestID",
                ""
            )
        )

        payment.save()

        return Response(result)
    
class MpesaCallbackView(
    generics.CreateAPIView
):

    permission_classes = [
        AllowAny
    ]

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        body = request.data

        callback = (
            body["Body"]
            ["stkCallback"]
        )

        checkout_id = (
            callback[
                "CheckoutRequestID"
            ]
        )

        result_code = (
            callback[
                "ResultCode"
            ]
        )

        payment = (
            Payment.objects.filter(
                checkout_request_id=
                checkout_id
            ).first()
        )

        if not payment:

            return Response(
                {"message":
                 "Payment not found"}
            )

        if str(result_code) != "0":

            payment.status = "FAILED"

            payment.save()

            return Response(
                {"message":
                 "Failed"}
            )