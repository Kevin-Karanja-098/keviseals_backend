from rest_framework import generics, serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.conf import settings
from accounts.models import LandlordProfile
from .models import *
from .serializers import *
from .permissions import *

# Import the centralized notification hooks directly
from .notifications_hooks import (
    notify_property_created,
    notify_property_updated,
    notify_unit_created,
    notify_unit_updated,
    notify_unit_status_changed
)

# --- PROPERTY VIEWS ---

class PropertyCreateView(generics.CreateAPIView):
    serializer_class = PropertyCreateSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def perform_create(self, serializer):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        property_instance = serializer.save(landlord=landlord)
        
        # Trigger real-time property listing alerts
        notify_property_created(property_instance)

class MyPropertiesView(generics.ListAPIView):
    serializer_class = PropertyListSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):
        return Property.objects.filter(landlord=LandlordProfile.objects.get(user=self.request.user)).order_by("-created_at")

class PropertyDetailView(generics.RetrieveAPIView):
    serializer_class = PropertyDetailSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]
    lookup_field = "pk"

    def get_queryset(self):
        return Property.objects.filter(landlord=LandlordProfile.objects.get(user=self.request.user))

class PropertyUpdateView(generics.UpdateAPIView):
    serializer_class = PropertyCreateSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]
    lookup_field = "pk"

    def get_queryset(self):
        return Property.objects.filter(landlord=LandlordProfile.objects.get(user=self.request.user))

    def perform_update(self, serializer):
        property_instance = serializer.save()
        # Trigger notice if status or profile configuration details shift
        notify_property_updated(property_instance)

class PropertyDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsActiveLandlord]
    lookup_field = "pk"

    def get_queryset(self):
        return Property.objects.filter(landlord=LandlordProfile.objects.get(user=self.request.user))


# --- PROPERTY MEDIA VIEWS ---

class PropertyMediaUploadView(generics.CreateAPIView):
    serializer_class = PropertyMediaUploadSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def perform_create(self, serializer):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        property_instance = Property.objects.filter(id=self.request.data.get("property"), landlord=landlord).first()
        if not property_instance:
            raise serializers.ValidationError({"error": "Property not found."})
        serializer.save(property=property_instance)

class PropertyMediaListView(generics.ListAPIView):
    serializer_class = PropertyMediaSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        return PropertyMedia.objects.filter(property__id=self.kwargs["property_id"], property__landlord=landlord)

class PropertyMediaDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsActiveLandlord]
    lookup_field = "pk"

    def get_queryset(self):
        return PropertyMedia.objects.filter(property__landlord=LandlordProfile.objects.get(user=self.request.user))


# --- PROPERTY RULES VIEWS ---

class PropertyRuleCreateView(generics.CreateAPIView):
    serializer_class = PropertyRuleSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def perform_create(self, serializer):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        property_instance = Property.objects.filter(id=self.request.data.get("property"), landlord=landlord).first()
        if not property_instance:
            raise serializers.ValidationError({"error": "Property not found"})
        serializer.save(property=property_instance)

class PropertyRuleListView(generics.ListAPIView):
    serializer_class = PropertyRuleSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        return PropertyRule.objects.filter(property__id=self.kwargs["property_id"], property__landlord=landlord)


# --- UNIT VIEWS ---

class UnitCreateView(generics.CreateAPIView):
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def perform_create(self, serializer):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        property_obj = Property.objects.filter(id=self.request.data.get("property"), landlord=landlord).first()
        if not property_obj:
            raise serializers.ValidationError({"error": "Property not found"})
        unit_instance = serializer.save(property=property_obj)
        
        # Trigger alert for newly registered units
        notify_unit_created(unit_instance)

class UnitListView(generics.ListAPIView):
    serializer_class = UnitListSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):
        return Unit.objects.filter(property__landlord=LandlordProfile.objects.get(user=self.request.user)).order_by("-created_at")

class UnitDetailView(generics.RetrieveAPIView):
    serializer_class = UnitDetailSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):
        return Unit.objects.filter(property__landlord=LandlordProfile.objects.get(user=self.request.user))

class UnitUpdateView(generics.UpdateAPIView):
    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):
        return Unit.objects.filter(property__landlord=LandlordProfile.objects.get(user=self.request.user))

    def perform_update(self, serializer):
        # Capture database image state prior to verification
        old_instance = self.get_object()
        old_status = old_instance.occupancy_status
        
        unit_instance = serializer.save()
        
        # Dispatch alerts conditionally based on updates
        if old_status != unit_instance.occupancy_status:
            notify_unit_status_changed(unit_instance, old_status)
        else:
            notify_unit_updated(unit_instance)

class UnitDeleteView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):
        return Unit.objects.filter(property__landlord=LandlordProfile.objects.get(user=self.request.user))


# --- UNIT MEDIA VIEWS ---

class UnitMediaUploadView(generics.CreateAPIView):
    serializer_class = UnitMediaSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def perform_create(self, serializer):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        unit = Unit.objects.filter(id=self.request.data.get("unit"), property__landlord=landlord).first()
        if not unit:
            raise serializers.ValidationError({"error": "Unit not found"})
        serializer.save(unit=unit)

class UnitMediaListView(generics.ListAPIView):
    serializer_class = UnitMediaSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):
        landlord = LandlordProfile.objects.get(user=self.request.user)
        return UnitMedia.objects.filter(unit_id=self.kwargs["unit_id"], unit__property__landlord=landlord)


# --- PUBLIC VIEWS ---

class PublicUnitListView(generics.ListAPIView):
    serializer_class = PublicUnitSerializer
    permission_classes = []

    def get_queryset(self):
        return Unit.objects.filter(property_id=self.kwargs["property_id"], occupancy_status="AVAILABLE")