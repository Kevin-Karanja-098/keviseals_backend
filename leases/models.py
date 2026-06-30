import secrets
from django.db import models
from accounts.models import *
from properties.models import Unit
from django.db.models import Sum


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
    entry_code = models.CharField(max_length=50, unique=True,null=True,blank=True,)
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


class MoveOutRequest(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled"),
    ]

    completed_at = models.DateTimeField(
        null=True,
        blank=True
    )

    lease = models.ForeignKey(Lease, on_delete=models.CASCADE, related_name="move_out_requests")
    reason = models.TextField()
    requested_date = models.DateField()
    landlord_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.lease_id} - {self.status}"


class PropertyInspection(models.Model):
    STATUS_CHOICES = [("DRAFT", "Draft"), ("COMPLETED", "Completed")]

    move_out_request = models.OneToOneField(MoveOutRequest, on_delete=models.CASCADE, related_name="inspection")
    inspected_by = models.ForeignKey(LandlordProfile, on_delete=models.CASCADE, related_name="property_inspections")
    inspection_date = models.DateField(auto_now_add=True)
    general_notes = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def total_damage(self):
        return self.items.aggregate(total=Sum("amount"))["total"] or 0

    def __str__(self):
        return f"Inspection {self.id}"


class InspectionItem(models.Model):
    inspection = models.ForeignKey(PropertyInspection, on_delete=models.CASCADE, related_name="items")
    item_name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.item_name

class LeaseSettlement(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("WAITING_FOR_TENANT_PAYMENT", "Waiting For Tenant Payment"),
        ("WAITING_FOR_REFUND", "Waiting For Refund"),
        ("FINANCIALLY_SETTLED", "Financially Settled"),
        ("FINALIZED", "Finalized"),
    ]

    inspection = models.OneToOneField(PropertyInspection, on_delete=models.CASCADE, related_name="settlement")
    deposit_amount = models.DecimalField(max_digits=12, decimal_places=2)
    wallet_credit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    outstanding_rent = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    damage_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_owed = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="PENDING")
    refund_paid = models.BooleanField(default=False)
    refund_paid_at = models.DateTimeField(null=True, blank=True)
    balance_received = models.BooleanField(default=False)
    balance_received_at = models.DateTimeField(null=True, blank=True)
    payment_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

class SettlementTransaction(models.Model):
    TYPE_CHOICES = [("COLLECTION", "Collection"), ("REFUND", "Refund")]
    METHOD_CHOICES = [("MPESA_STK", "M-Pesa STK"), ("MPESA_B2C", "M-Pesa B2C"), ("BANK", "Bank Transfer"), ("CASH", "Cash")]
    STATUS_CHOICES = [("PENDING", "Pending"), ("SUCCESS", "Success"), ("FAILED", "Failed")]

    settlement = models.ForeignKey(LeaseSettlement, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    payment_method = models.CharField(max_length=20, choices=METHOD_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    phone_number = models.CharField(max_length=20, blank=True)
    checkout_request_id = models.CharField(max_length=255, blank=True)
    merchant_request_id = models.CharField(max_length=255, blank=True)
    mpesa_receipt = models.CharField(max_length=255, blank=True)
    reference = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)

    conversation_id = models.CharField(
        max_length=120,
        blank=True
    )

    originator_conversation_id = models.CharField(
        max_length=120,
        blank=True
    )

    result_code = models.CharField(
        max_length=20,
        blank=True
    )

    result_desc = models.TextField(
        blank=True
    )

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount}"