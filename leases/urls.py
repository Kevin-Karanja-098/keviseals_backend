from django.urls import path
from .views import *

urlpatterns = [
    path("requests/create/", LeaseRequestCreateView.as_view()),
    path("requests/my/", MyLeaseRequestsView.as_view()),
    path("requests/landlord/", LandlordLeaseRequestListView.as_view()),
    path("requests/<int:pk>/approve/", ApproveLeaseRequestView.as_view()),
    path("requests/<int:pk>/reject/", RejectLeaseRequestView.as_view()),
    path("payments/lease-request/", InitiateLeaseRequestPaymentView.as_view()),
    path("payments/wallet/", InitiateLeaseWalletPaymentView.as_view()),
    path("payments/callback/", MpesaCallbackView.as_view()),
    path("billing/process/",BillingCronView.as_view()),
]