from django.urls import path

from .views import *

urlpatterns = [

    path(
        "register/landlord/",
        LandlordRegistrationView.as_view()
    ),

    path(
        "register/tenant/",
        TenantRegistrationView.as_view()
    ),

    path(
        "verify-otp/",
        VerifyOTPView.as_view()
    ),

    path(
    "logout/",
    LogoutView.as_view()
),

    path(
    "resend-otp/",
    ResendOTPView.as_view()
),

    path(
        "login/",
        LoginView.as_view()
    ),

    path(
        "profile/",
        ProfileView.as_view()
    ),

   

path(
    "landlord/theme/",
    LandlordThemeView.as_view()
),

path(
    "landlord/generate-contract/",
    GenerateContractView.as_view()
),

path(
    "landlord/upload-contract/",
    UploadContractView.as_view()
),

path(
    "contracts/<int:pk>/approve/",
    ApproveContractView.as_view()
),

path(
    "contracts/<int:pk>/reject/",
    RejectContractView.as_view()
),
]