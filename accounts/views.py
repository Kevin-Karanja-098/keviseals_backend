from datetime import timedelta
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, EmailVerificationOTP
from .permissions import *
from .serializers import *
from .services import *
from .emails import*
from .notification_service import *

class BaseRegistrationView(generics.CreateAPIView):
    def perform_create(self, serializer):
        user = serializer.save()
        otp = generate_otp()

        EmailVerificationOTP.objects.create(
            user=user,
            otp=otp,
            expires_at=timezone.now() + timedelta(minutes=10)
        )

        send_registration_email(user)
        send_otp_email(user, otp)
        notify_registration(user)
        if user.role == "LANDLORD":
            notify_new_landlord_registration(user)
        else:
            notify_new_tenant_registration(user)


class LandlordRegistrationView(BaseRegistrationView):
    serializer_class = LandlordRegistrationSerializer

class TenantRegistrationView(BaseRegistrationView):
    serializer_class = TenantRegistrationSerializer

class VerifyOTPView(generics.CreateAPIView):
    serializer_class = VerifyOTPSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if not user:
            return Response({"error": "Invalid user request."}, status=status.HTTP_400_BAD_REQUEST)
        record = EmailVerificationOTP.objects.filter(user=user, otp=serializer.validated_data["otp"], is_used=False).first()
        if not record:
            return Response({"error": "Invalid OTP"}, status=400)
        if timezone.now() > record.expires_at:
            return Response({"error": "OTP expired"}, status=400)
        if not record:
            return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
        record.is_used = True
        record.save()
        user.is_email_verified = True
        user.save()

        send_email_verified_email(user)
        notify_email_verified(user)

        return Response(
            {"message": "Email verified"},
            status=status.HTTP_200_OK
        )

class LoginView(generics.CreateAPIView):
    serializer_class = LoginSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if not user or not user.check_password(serializer.validated_data["password"]):
            return Response({"error": "Invalid credentials"}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_email_verified:
            return Response({"error": "Verify email first"}, status=status.HTTP_400_BAD_REQUEST)
        refresh = RefreshToken.for_user(user)
        return Response({"refresh": str(refresh), "access": str(refresh.access_token), "role": user.role}, status=status.HTTP_200_OK)

class ProfileView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    def get_serializer_class(self):
        if self.request.user.role == "LANDLORD": return LandlordProfileSerializer
        if self.request.user.role == "TENANT": return TenantProfileSerializer
        return super().get_serializer_class()
    def get_object(self):
        user = self.request.user
        if user.role == "LANDLORD":
            profile = LandlordProfile.objects.filter(user=user).first()
            if not profile: raise generics.ValidationError({"error": "Landlord profile record missing."})
            return profile
        if user.role == "TENANT":
            profile = TenantProfile.objects.filter(user=user).first()
            if not profile: raise generics.ValidationError({"error": "Tenant profile record missing."})
            return profile
        return user

class ResendOTPView(generics.CreateAPIView):
    serializer_class = ResendOTPSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = User.objects.filter(email=serializer.validated_data["email"]).first()
        if not user: return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        otp = generate_otp()
        EmailVerificationOTP.objects.create(user=user, otp=otp, expires_at=timezone.now() + timedelta(minutes=10))
        try: send_otp_email(user.email, otp)
        except Exception as e: print(f"Failed to resend email background dispatch: {e}")
        return Response({"message": "OTP resent"}, status=status.HTTP_200_OK)

class LogoutView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data["refresh"]).blacklist()
            return Response({"message": "Logged out"}, status=status.HTTP_200_OK)
        except Exception:
            return Response({"error": "Invalid or already blacklisted token"}, status=status.HTTP_400_BAD_REQUEST)

class LandlordThemeView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated, IsLandlord]
    serializer_class = LandlordThemeSerializer
    def get_object(self):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        theme, _ = LandlordTheme.objects.get_or_create(landlord=landlord)
        return theme

class GenerateContractView(generics.CreateAPIView):
    permission_classes = [IsAuthenticated, IsLandlord]
    def create(self, request, *args, **kwargs):
        landlord = LandlordProfile.objects.get(user=request.user)
        contract, _ = LandlordContract.objects.get_or_create(landlord=landlord)
        generate_landlord_contract_pdf(contract)
        send_contract_generated_email(request.user)
        notify_contract_generated(request.user)
        return Response({"message": "Contract generated", "contract_id": contract.id, "pdf": contract.generated_contract.url})

class UploadContractView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsLandlord]
    serializer_class = ContractUploadSerializer
    def get_object(self):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        return LandlordContract.objects.get(landlord=landlord)
    def perform_update(self, serializer):

        contract = serializer.save()

        user = contract.landlord.user

        send_contract_uploaded_email(user)

        notify_contract_uploaded(user)

        notify_contract_uploaded_to_admin(user)

class ApproveContractView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsPropertyManager]
    def update(self, request, *args, **kwargs):
        contract = LandlordContract.objects.get(id=kwargs["pk"])
        contract.status = "APPROVED"
        contract.save()
        landlord = contract.landlord
        landlord.status = "ACTIVE"
        landlord.save()
        send_contract_approved_email(landlord.user)

        notify_contract_approved(landlord.user)
        return Response({"message": "Contract approved"})

class RejectContractView(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated, IsPropertyManager]
    def update(self, request, *args, **kwargs):
        contract = LandlordContract.objects.get(id=kwargs["pk"])
        contract.status = "REJECTED"
        contract.save()
        send_contract_rejected_email(contract.landlord.user)

        notify_contract_rejected(contract.landlord.user)
        return Response({"message": "Contract rejected"})