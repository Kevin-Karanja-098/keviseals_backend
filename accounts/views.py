from datetime import timedelta
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User, EmailVerificationOTP
from .permissions import*
from .serializers import*
from .services import *
from .utils import send_otp_email


class BaseRegistrationView(generics.CreateAPIView):
    """
    Base generic view to handle shared user registration and OTP logic.
    Using CreateAPIView automatically generates a form in the DRF browsable API.
    """
    def perform_create(self, serializer):
        # Save the user instance created by the serializer
        user = serializer.save()

        # Generate and assign OTP
        otp = generate_otp()
        EmailVerificationOTP.objects.create(
            user=user,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Send notification out-of-band
        send_otp_email(user.email, otp)


class LandlordRegistrationView(BaseRegistrationView):
    serializer_class = LandlordRegistrationSerializer


class TenantRegistrationView(BaseRegistrationView):
    serializer_class = TenantRegistrationSerializer


class VerifyOTPView(generics.CreateAPIView):
    serializer_class = VerifyOTPSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data["email"]
        otp = serializer.validated_data["otp"]

        # Safely fetch user or return early if missing
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"error": "Invalid user request."}, status=status.HTTP_400_BAD_REQUEST)

        record = EmailVerificationOTP.objects.filter(
            user=user,
            otp=otp,
            is_used=False
        ).first()

        if not record:
            return Response(
                {"error": "Invalid OTP"},
                status=400
            )

        if timezone.now() > record.expires_at:
            return Response(
                {"error": "OTP expired"},
                status=400
            )

        if not record:
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)

        # Mark token and user as verified
        record.is_used = True
        record.save()

        user.is_email_verified = True
        user.save()

        return Response({"message": "Email verified"}, status=status.HTTP_200_OK)


class LoginView(generics.CreateAPIView):
    serializer_class = LoginSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        user = User.objects.filter(email=email).first()

        if not user or not user.check_password(password):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)

        if not user.is_email_verified:
            return Response({"error": "Verify email first"}, status=status.HTTP_400_BAD_REQUEST)

        refresh = RefreshToken.for_user(user)

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "role": user.role
        }, status=status.HTTP_200_OK)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Generic view to dynamically retrieve the logged-in user's profile
    based on their designated organizational role (Landlord or Tenant).
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """
        Dynamically returns the appropriate serializer based on user role.
        """
        if self.request.user.role == "LANDLORD":
            return LandlordProfileSerializer
        elif self.request.user.role == "TENANT":
            return TenantProfileSerializer
        
        # Fallback if a Superadmin/Property Manager hits this endpoint without a profile
        return super().get_serializer_class()

    def get_object(self):
        """
        Overridden to target and extract the specific profile model instance 
        directly bound to the authenticated user token.
        """
        user = self.request.user

        if user.role == "LANDLORD":
            # Using filter().first() handles edge cases where a profile might not exist yet
            profile = LandlordProfile.objects.filter(user=user).first()
            if not profile:
                raise generics.ValidationError({"error": "Landlord profile record missing."})
            return profile

        if user.role == "TENANT":
            profile = TenantProfile.objects.filter(user=user).first()
            if not profile:
                raise generics.ValidationError({"error": "Tenant profile record missing."})
            return profile

        # Handle fallback for general users or platform managers who don't have secondary profiles
        return user
    

class ResendOTPView(generics.CreateAPIView):
    """
    Generic view to handle resending OTP codes.
    Using CreateAPIView enables form inputs dynamically in the browsable API.
    """
    serializer_class = ResendOTPSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]

        # Fetch the user matching the email
        user = User.objects.filter(email=email).first()

        if not user:
            return Response(
                {"error": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate and save a new OTP
        otp = generate_otp()
        EmailVerificationOTP.objects.create(
            user=user,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        # Safely try sending the email notification
        try:
            send_otp_email(user.email, otp)
        except Exception as e:
            print(f"Failed to resend email background dispatch: {e}")

        return Response(
            {"message": "OTP resent"}, 
            status=status.HTTP_200_OK
        )
    
class LogoutView(generics.CreateAPIView):
    """
    Generic view to handle JWT logout by blacklisting the provided refresh token.
    Requires authentication and provides an input form in the browsable API.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        try:
            # Initialize the token and add it to the database blacklist
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {"message": "Logged out"}, 
                status=status.HTTP_200_OK
            )
        except Exception:
            # Handles edge cases where the token is already invalid or expired
            return Response(
                {"error": "Invalid or already blacklisted token"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
class LandlordThemeView(
    generics.RetrieveUpdateAPIView
):

    permission_classes = [
        IsAuthenticated,
        IsLandlord
    ]

    serializer_class = (
        LandlordThemeSerializer
    )

    def get_object(self):

        landlord = LandlordProfile.objects.get(
            user=self.request.user
        )

        theme, _ = (
            LandlordTheme.objects.get_or_create(
                landlord=landlord
            )
        )

        return theme
    
class GenerateContractView(
    generics.CreateAPIView
):

    permission_classes = [
        IsAuthenticated,
        IsLandlord
    ]

    def create(
        self,
        request,
        *args,
        **kwargs
    ):

        landlord = (
            LandlordProfile.objects.get(
                user=request.user
            )
        )

        contract, _ = (
            LandlordContract.objects.get_or_create(
                landlord=landlord
            )
        )

        generate_landlord_contract_pdf(
            contract
        )

        return Response({
            "message":
            "Contract generated",
            "contract_id":
            contract.id,
            "pdf":
            contract.generated_contract.url
        })
    
class UploadContractView(
    generics.UpdateAPIView
):

    permission_classes = [
        IsAuthenticated,
        IsLandlord
    ]

    serializer_class = (
        ContractUploadSerializer
    )

    def get_object(self):

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        return LandlordContract.objects.get(
            landlord=landlord
        )
    
class ApproveContractView(
    generics.UpdateAPIView
):

    permission_classes = [
        IsAuthenticated,
        IsPropertyManager
    ]

    def update(
        self,
        request,
        *args,
        **kwargs
    ):

        contract = (
            LandlordContract.objects.get(
                id=kwargs["pk"]
            )
        )

        contract.status = "APPROVED"
        contract.save()

        landlord = contract.landlord

        landlord.status = "ACTIVE"
        landlord.save()

        return Response({
            "message":
            "Contract approved"
        })
    
class UploadContractView(
    generics.UpdateAPIView
):

    permission_classes = [
        IsAuthenticated,
        IsLandlord
    ]

    serializer_class = (
        ContractUploadSerializer
    )

    def get_object(self):

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        return LandlordContract.objects.get(
            landlord=landlord
        )
    
class RejectContractView(
    generics.UpdateAPIView
):

    permission_classes = [
        IsAuthenticated,
        IsPropertyManager
    ]

    def update(
        self,
        request,
        *args,
        **kwargs
    ):

        contract = (
            LandlordContract.objects.get(
                id=kwargs["pk"]
            )
        )

        contract.status = "REJECTED"
        contract.save()

        return Response({
            "message":
            "Contract rejected"
        })