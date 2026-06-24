from django.db import models
from accounts.models import LandlordProfile, TenantProfile
from django.contrib.gis.db import models  # <-- CRITICAL: Use the GIS model layer!



# Create your models here.
class Property(models.Model):

    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('INACTIVE', 'Inactive'),
    )

    landlord = models.ForeignKey(
        LandlordProfile,
        on_delete=models.CASCADE,
        related_name='properties'
    )

    name = models.CharField(
        max_length=255
    )

    description = models.TextField()

    county = models.CharField(
        max_length=100
    )

    town = models.CharField(
        max_length=100
    )

    address = models.TextField()

    location = models.PointField(srid=4326, geography=True, null=True, blank=True)

    cover_image = models.ImageField(
        upload_to='properties/covers/',
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ACTIVE'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name

class PropertyMedia(models.Model):

    MEDIA_CHOICES = (
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='media'
    )

    file = models.FileField(
        upload_to='properties/media/'
    )

    media_type = models.CharField(
        max_length=20,
        choices=MEDIA_CHOICES
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.property.name} - {self.media_type}"

class PropertyRule(models.Model):

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='rules'
    )

    title = models.CharField(
        max_length=255
    )

    description = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

class Block(models.Model):

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='blocks'
    )

    name = models.CharField(
        max_length=50
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name

class Unit(models.Model):

    STATUS_CHOICES = (
        ('AVAILABLE', 'Available'),
        ('RESERVED', 'Reserved'),
        ('OCCUPIED', 'Occupied'),
        ('MAINTENANCE', 'Maintenance'),
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.CASCADE,
        related_name='units'
    )

    block = models.ForeignKey(
        Block,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='units'
    )

    unit_number = models.CharField(
        max_length=50
    )

    title = models.CharField(max_length=255, default="Untitled Unit")

    description = models.TextField(
        blank=True
    )

    bedrooms = models.PositiveIntegerField(
        default=1
    )

    bathrooms = models.PositiveIntegerField(
        default=1
    )

    square_feet = models.PositiveIntegerField(
        null=True,
        blank=True
    )

    monthly_rent = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    security_deposit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0
    )

    occupancy_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='AVAILABLE'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        unique_together = (
            'property',
            'unit_number'
        )

    def __str__(self):
        return f"{self.property.name} - {self.unit_number}"

class UnitMedia(models.Model):

    MEDIA_CHOICES = (
        ('IMAGE', 'Image'),
        ('VIDEO', 'Video'),
    )

    unit = models.ForeignKey(
        Unit,
        on_delete=models.CASCADE,
        related_name='media'
    )

    file = models.FileField(
        upload_to='units/media/'
    )

    media_type = models.CharField(
        max_length=20,
        choices=MEDIA_CHOICES
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

