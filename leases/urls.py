from django.urls import path
from .views import *

urlpatterns = [
    # Lease Requests
    path("requests/create/", LeaseRequestCreateView.as_view()),
    path("requests/my/", MyLeaseRequestsView.as_view()),
    path("requests/landlord/", LandlordLeaseRequestListView.as_view()),
    path("requests/<int:pk>/approve/", ApproveLeaseRequestView.as_view()),
    path("requests/<int:pk>/reject/", RejectLeaseRequestView.as_view()),

    # Payments & Billing
    path("payments/lease-request/", InitiateLeaseRequestPaymentView.as_view()),
    path("payments/wallet/", InitiateLeaseWalletPaymentView.as_view()),
    path("payments/callback/", MpesaCallbackView.as_view()),
    path("billing/process/", BillingCronView.as_view()),

    # Move Out Requests
    path("move-out/create/", CreateMoveOutRequestView.as_view()),
    path("move-out/my/", MyMoveOutRequestsView.as_view()),
    path("move-out/landlord/", LandlordMoveOutRequestsView.as_view()),
    path("move-out/<int:pk>/approve/", ApproveMoveOutRequestView.as_view()),
    path("move-out/<int:pk>/reject/", RejectMoveOutRequestView.as_view()),
    path("move-out/<int:pk>/cancel/", CancelMoveOutRequestView.as_view()),
]