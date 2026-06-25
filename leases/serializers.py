from rest_framework import serializers
from .models import *

class LeaseRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseRequest
        fields = "__all__"
        read_only_fields = ("tenant", "amount_paid", "required_amount", "status")

class LeaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lease
        fields = "__all__"

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"

class LeaseWalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeaseWallet
        fields = "__all__"

class RentChargeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RentCharge
        fields = "__all__"