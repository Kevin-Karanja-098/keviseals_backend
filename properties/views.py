from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from accounts.models import (
    LandlordProfile
)

from .models import *
from .serializers import *
from .permissions import *

class PropertyCreateView(
    generics.CreateAPIView
):

    serializer_class = (
        PropertyCreateSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsActiveLandlord
    ]

    def perform_create(
        self,
        serializer
    ):

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        serializer.save(
            landlord=landlord
        )

class MyPropertiesView(
    generics.ListAPIView
):

    serializer_class = (
        PropertyListSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsActiveLandlord
    ]

    def get_queryset(self):

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        return Property.objects.filter(
            landlord=landlord
        ).order_by(
            "-created_at"
        )
    
class PropertyDetailView(
    generics.RetrieveAPIView
):

    serializer_class = (
        PropertyDetailSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsActiveLandlord
    ]

    lookup_field = "pk"

    def get_queryset(self):

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        return Property.objects.filter(
            landlord=landlord
        )
    
class PropertyUpdateView(
    generics.UpdateAPIView
):

    serializer_class = (
        PropertyCreateSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsActiveLandlord
    ]

    lookup_field = "pk"

    def get_queryset(self):

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        return Property.objects.filter(
            landlord=landlord
        )
    
class PropertyDeleteView(
    generics.DestroyAPIView
):

    permission_classes = [
        IsAuthenticated,
        IsActiveLandlord
    ]

    lookup_field = "pk"

    def get_queryset(self):

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        return Property.objects.filter(
            landlord=landlord
        )
    
class PropertyMediaUploadView(
    generics.CreateAPIView
):

    serializer_class = (
        PropertyMediaUploadSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsActiveLandlord
    ]

    def perform_create(
        self,
        serializer
    ):

        property_id = self.request.data.get(
            "property"
        )

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        property_instance = (
            Property.objects.filter(
                id=property_id,
                landlord=landlord
            ).first()
        )

        if not property_instance:
            raise serializers.ValidationError(
                {
                    "error":
                    "Property not found."
                }
            )

        serializer.save(
            property=property_instance
        )

class PropertyMediaListView(
    generics.ListAPIView
):

    serializer_class = (
        PropertyMediaSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsActiveLandlord
    ]

    def get_queryset(self):

        property_id = self.kwargs["property_id"]

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        return PropertyMedia.objects.filter(
            property__id=property_id,
            property__landlord=landlord
        )
    
class PropertyMediaDeleteView(
    generics.DestroyAPIView
):

    permission_classes = [
        IsAuthenticated,
        IsActiveLandlord
    ]

    lookup_field = "pk"

    def get_queryset(self):

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        return PropertyMedia.objects.filter(
            property__landlord=landlord
        )

class PropertyRuleCreateView(
    generics.CreateAPIView
):

    serializer_class = (
        PropertyRuleSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsActiveLandlord
    ]

    def perform_create(
        self,
        serializer
    ):

        property_id = self.request.data.get(
            "property"
        )

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        property_instance = (
            Property.objects.filter(
                id=property_id,
                landlord=landlord
            ).first()
        )

        if not property_instance:
            raise serializers.ValidationError(
                {
                    "error":
                    "Property not found"
                }
            )

        serializer.save(
            property=property_instance
        )

class PropertyRuleListView(
    generics.ListAPIView
):

    serializer_class = (
        PropertyRuleSerializer
    )

    permission_classes = [
        IsAuthenticated,
        IsActiveLandlord
    ]

    def get_queryset(self):

        property_id = self.kwargs["property_id"]

        landlord = (
            LandlordProfile.objects.get(
                user=self.request.user
            )
        )

        return PropertyRule.objects.filter(
            property__id=property_id,
            property__landlord=landlord
        )
    
class UnitCreateView(generics.CreateAPIView):

    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def perform_create(self, serializer):

        landlord = LandlordProfile.objects.get(
            user=self.request.user
        )

        property_id = self.request.data.get("property")

        property_obj = Property.objects.filter(
            id=property_id,
            landlord=landlord
        ).first()

        if not property_obj:
            raise Exception("Property not found")

        serializer.save(property=property_obj)

class UnitListView(generics.ListAPIView):

    serializer_class = UnitListSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):

        landlord = LandlordProfile.objects.get(
            user=self.request.user
        )

        return Unit.objects.filter(
            property__landlord=landlord
        ).order_by("-created_at")
    
class UnitDetailView(generics.RetrieveAPIView):

    serializer_class = UnitDetailSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):

        landlord = LandlordProfile.objects.get(
            user=self.request.user
        )

        return Unit.objects.filter(
            property__landlord=landlord
        )
    
class UnitUpdateView(generics.UpdateAPIView):

    serializer_class = UnitSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):

        landlord = LandlordProfile.objects.get(
            user=self.request.user
        )

        return Unit.objects.filter(
            property__landlord=landlord
        )
    
class UnitDeleteView(generics.DestroyAPIView):

    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):

        landlord = LandlordProfile.objects.get(
            user=self.request.user
        )

        return Unit.objects.filter(
            property__landlord=landlord
        )
    
class UnitMediaUploadView(generics.CreateAPIView):

    serializer_class = UnitMediaSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def perform_create(self, serializer):

        landlord = LandlordProfile.objects.get(
            user=self.request.user
        )

        unit_id = self.request.data.get("unit")

        unit = Unit.objects.filter(
            id=unit_id,
            property__landlord=landlord
        ).first()

        if not unit:
            raise Exception("Unit not found")

        serializer.save(unit=unit)

class UnitMediaListView(generics.ListAPIView):

    serializer_class = UnitMediaSerializer
    permission_classes = [IsAuthenticated, IsActiveLandlord]

    def get_queryset(self):

        unit_id = self.kwargs["unit_id"]

        landlord = LandlordProfile.objects.get(
            user=self.request.user
        )

        return UnitMedia.objects.filter(
            unit_id=unit_id,
            unit__property__landlord=landlord
        )
    
class PublicUnitListView(generics.ListAPIView):

    serializer_class = PublicUnitSerializer
    permission_classes = []

    def get_queryset(self):

        property_id = self.kwargs["property_id"]

        return Unit.objects.filter(
            property_id=property_id,
            occupancy_status="AVAILABLE"
        )