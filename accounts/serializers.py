from rest_framework import serializers
from .models import *


class LandlordRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    national_id = serializers.CharField(write_only=True)

    id_front = serializers.ImageField(
        write_only=True
    )

    id_back = serializers.ImageField(
        write_only=True
    )

    profile_photo = serializers.ImageField(
        required=False,
        write_only=True
    )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists"
            )
        return value

    def validate_phone_number(self, value):
        if User.objects.filter(
            phone_number=value
        ).exists():
            raise serializers.ValidationError(
                "Phone number already exists"
            )
        return value

    def create(self, validated_data):

        user = User.objects.create_user(
            email=validated_data["email"],
            phone_number=validated_data["phone_number"],
            password=validated_data["password"],
            role="LANDLORD"
        )

        LandlordProfile.objects.create(
            user=user,
            national_id=validated_data["national_id"],
            id_front=validated_data["id_front"],
            id_back=validated_data["id_back"],
            profile_photo=validated_data.get(
                "profile_photo"
            )
        )

        return user

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "email": instance.email,
            "phone_number": instance.phone_number,
            "role": instance.role,
            "message": "Landlord registered successfully"
        }

class TenantRegistrationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    national_id = serializers.CharField(
        write_only=True
    )

    id_front = serializers.ImageField(
        write_only=True
    )

    id_back = serializers.ImageField(
        write_only=True
    )

    profile_photo = serializers.ImageField(
        required=False,
        write_only=True
    )

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Email already exists"
            )
        return value

    def validate_phone_number(self, value):
        if User.objects.filter(
            phone_number=value
        ).exists():
            raise serializers.ValidationError(
                "Phone number already exists"
            )
        return value

    def create(self, validated_data):

        user = User.objects.create_user(
            email=validated_data["email"],
            phone_number=validated_data["phone_number"],
            password=validated_data["password"],
            role="TENANT"
        )

        TenantProfile.objects.create(
            user=user,
            national_id=validated_data["national_id"],
            id_front=validated_data["id_front"],
            id_back=validated_data["id_back"],
            profile_photo=validated_data.get(
                "profile_photo"
            )
        )

        return user

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "email": instance.email,
            "phone_number": instance.phone_number,
            "role": instance.role,
            "message": "Tenant registered successfully"
        }




class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "phone_number",
            "role",
            "is_email_verified"
        )

class LandlordProfileSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LandlordProfile

        fields = "__all__"

class TenantProfileSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = TenantProfile

        fields = "__all__"

class ResendOTPSerializer(serializers.Serializer):

    email = serializers.EmailField()

class LogoutSerializer(serializers.Serializer):

    refresh = serializers.CharField()

class LandlordThemeSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LandlordTheme

        fields = "__all__"

        read_only_fields = (
            "landlord",
        )

class ContractUploadSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LandlordContract

        fields = (
            "signed_contract",
            "digital_signature",
        )