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

class MoveOutRequestSerializer(serializers.ModelSerializer):

    class Meta:
        model = MoveOutRequest
        fields = "__all__"
        read_only_fields = (
            "lease",
            "status",
            "landlord_notes",
        )

class InspectionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InspectionItem
        fields = "__all__"


class PropertyInspectionSerializer(serializers.ModelSerializer):
    total_damage = serializers.ReadOnlyField()
    items = InspectionItemSerializer(many=True, read_only=True)

    class Meta:
        model = PropertyInspection
        fields = "__all__"
        read_only_fields = (
            "inspected_by",
            "move_out_request",
            "status",
            "general_notes",
            "created_at",
            "total_damage",
        )

class SettlementTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = SettlementTransaction
        fields = "__all__"