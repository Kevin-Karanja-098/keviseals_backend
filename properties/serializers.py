from rest_framework import serializers
from .models import *

class PropertySerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        exclude = ('landlord',)

class BlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Block
        fields = '__all__'

class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = "__all__"
        read_only_fields = ("occupancy_status",)

class UnitListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ("id", "property", "unit_number", "title", "monthly_rent", "occupancy_status")

class UnitDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = "__all__"

class PropertyCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        exclude = ("landlord",)

class PropertyListSerializer(serializers.ModelSerializer):
    total_units = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = ("id", "name", "county", "town", "cover_image", "status", "total_units", "created_at")

    def get_total_units(self, obj):
        return obj.units.count()

class PropertyDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = Property
        fields = "__all__"

class PropertyMediaUploadSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyMedia
        fields = ("id", "property", "file", "media_type")

class PropertyMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyMedia
        fields = "__all__"

class PropertyRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = PropertyRule
        fields = "__all__"

class UnitMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnitMedia
        fields = "__all__"

class PublicUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ("id", "unit_number", "title", "monthly_rent", "bedrooms", "bathrooms", "occupancy_status")