import secrets
from django.db import models
from accounts.models import TenantProfile
from properties.models import Unit

class LeaseRequest(models.Model):
    STATUS_CHOICES = (('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'))

    tenant = models.ForeignKey(TenantProfile, on_delete=models.CASCADE, related_name='lease_requests')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name="property_lease_requests")
    deposit_required = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    rent_required = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    required_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    landlord_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class Lease(models.Model):
    STATUS_CHOICES = (('ACTIVE', 'Active'), ('COMPLETED', 'Completed'), ('TERMINATED', 'Terminated'))

    tenant = models.ForeignKey(TenantProfile, on_delete=models.CASCADE, related_name='leases')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='leases')
    entry_code = models.CharField(max_length=50, unique=True)
    move_in_date = models.DateField()
    move_out_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)
    deposit_held = models.DecimalField(max_digits=12,decimal_places=2,default=0)
    last_billing_date = models.DateTimeField(null=True,blank=True)

class LeaseWallet(models.Model):
    lease = models.OneToOneField(Lease, on_delete=models.CASCADE, related_name='wallet')
    available_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

class RentCharge(models.Model):
    STATUS_CHOICES = (('PAID', 'Paid'), ('PARTIAL', 'Partial'), ('UNPAID', 'Unpaid'))

    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name='charges')
    billing_month = models.DateField()
    due_date = models.DateField()
    rent_amount = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="UNPAID")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["billing_month"]
        #unique_together = ("lease", "billing_month")

class MoveOutRequest(models.Model):
    STATUS_CHOICES = (('PENDING', 'Pending'), ('APPROVED', 'Approved'), ('REJECTED', 'Rejected'))

    lease = models.ForeignKey(Lease, on_delete=models.CASCADE)
    reason = models.TextField()
    requested_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

class Payment(models.Model):
    STATUS_CHOICES = (('PENDING', 'Pending'), ('SUCCESS', 'Success'), ('FAILED', 'Failed'))

    tenant = models.ForeignKey(TenantProfile, on_delete=models.CASCADE, related_name='payments')
    lease_request = models.ForeignKey(LeaseRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    lease = models.ForeignKey(Lease, on_delete=models.SET_NULL, null=True, blank=True, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    checkout_request_id = models.CharField(max_length=255, blank=True)
    merchant_request_id = models.CharField(max_length=255, blank=True)
    mpesa_receipt = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.UUIDField(unique=True, null=True, blank=True)