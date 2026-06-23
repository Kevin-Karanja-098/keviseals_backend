from rest_framework import serializers

from .models import *

class LeaseRequestSerializer(
    serializers.ModelSerializer
):

    class Meta:

        model = LeaseRequest

        fields = "__all__"

        read_only_fields = (
            "tenant",
            "amount_paid",
            "required_amount",
            "status",
        )