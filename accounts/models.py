from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.base_user import BaseUserManager

class UserManager(BaseUserManager):
    def create_user(self, email, phone_number, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, phone_number, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "PROPERTY_MANAGER")
        extra_fields.setdefault("is_email_verified", True)
        return self.create_user(email=email, phone_number=phone_number, password=password, **extra_fields)
    
class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, unique=True)

    ROLE_CHOICES = (
        ('PROPERTY_MANAGER', 'Property Manager'),
        ('LANDLORD', 'Landlord'),
        ('TENANT', 'Tenant'),
    )
    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default='TENANT')
    is_email_verified = models.BooleanField(default=False)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["phone_number"]
    objects = UserManager()

class EmailVerificationOTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="email_otps")
    otp = models.CharField(max_length=6)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

class LandlordProfile(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    national_id = models.CharField(max_length=20, unique=True)
    profile_photo = models.ImageField(upload_to='landlords/profile_photos/', blank=True, null=True)
    id_front = models.ImageField(upload_to='landlords/id_front/', blank=True, null=True)
    id_back = models.ImageField(upload_to='landlords/id_back/', blank=True, null=True)
    company_name = models.CharField(max_length=255, blank=True)
    physical_address = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

class TenantProfile(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('VERIFIED', 'Verified'),
        ('REJECTED', 'Rejected'),
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    national_id = models.CharField(max_length=20, unique=True)
    profile_photo = models.ImageField(upload_to='tenants/profile_photos/', blank=True, null=True)
    id_front = models.ImageField(upload_to='tenants/id_front/', blank=True, null=True)
    id_back = models.ImageField(upload_to='tenants/id_back/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

class LandlordContract(models.Model):
    STATUS_CHOICES = (
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )
    landlord = models.OneToOneField(LandlordProfile, on_delete=models.CASCADE)
    generated_contract = models.FileField(upload_to='contracts/generated/', blank=True, null=True)
    signed_contract = models.FileField(upload_to='contracts/signed/', blank=True, null=True)
    digital_signature = models.ImageField(upload_to='contracts/signatures/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewed_contracts')
    reviewed_at = models.DateTimeField(null=True, blank=True)

class LandlordTheme(models.Model):
    landlord = models.OneToOneField(LandlordProfile, on_delete=models.CASCADE, related_name='theme')
    app_name = models.CharField(max_length=255, blank=True)
    primary_color = models.CharField(max_length=20, default='#00A651')
    secondary_color = models.CharField(max_length=20, default='#FFFFFF')
    heading_color = models.CharField(max_length=20, default='#000000')
    font_family = models.CharField(max_length=100, default='Poppins')
    logo = models.ImageField(upload_to='themes/logos/', blank=True, null=True)
    background_image = models.ImageField(upload_to='themes/backgrounds/', blank=True, null=True)