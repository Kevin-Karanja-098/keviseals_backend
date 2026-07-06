# Import notification services directly
from notifications.services import send_push_notification
from django.conf import settings
from django.core.mail import send_mail

# ==========================================
# NOTIFICATION UTILITIES & HELPER HOOKS
# ==========================================

def send_email_fallback(email, subject, body):
    """Utility helper to securely send transactional fallback emails."""
    try:
        send_mail(
            subject,
            body,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Email delivery failure: {e}")

# ==========================================
# LEASE REQUESTS & LEASE SIGNING HOOKS
# ==========================================

def notify_lease_request_created(lease_request):
    landlord = lease_request.unit.property.landlord.user
    tenant_name = lease_request.tenant.user.get_full_name() or lease_request.tenant.user.email
    unit_num = lease_request.unit.unit_number
    
    p_title = "New Lease Request"
    p_body = f"{tenant_name} has requested to lease Unit {unit_num}."
    send_push_notification(landlord, p_title, p_body, "lease", {"lease_request_id": str(lease_request.id)})
    send_email_fallback(landlord.email, "New Lease Request Received", p_body)

def notify_lease_approved(lease):
    tenant = lease.tenant.user
    unit_num = lease.unit.unit_number
    
    p_title = "Lease Request Approved"
    p_body = f"Congratulations! Your request for Unit {unit_num} has been approved, your entry code is {lease.entry_code}."
    send_push_notification(tenant, p_title, p_body, "lease", {"lease_id": str(lease.id)})
    send_email_fallback(tenant.email, "Your Lease Request Was Approved", p_body)
    
    code_title = "Entry Code Ready"
    code_body = f"Your access code is ready. Entry Code: {lease.entry_code}"
    send_push_notification(tenant, code_title, code_body, "lease", {"lease_id": str(lease.id)})
    send_email_fallback(tenant.email, "Your Lease Entry Code", code_body)

def notify_lease_rejected(lease_request):
    tenant = lease_request.tenant.user
    unit_num = lease_request.unit.unit_number
    p_body = f"Unfortunately your request for Unit {unit_num} was declined."
    send_push_notification(tenant, "Lease Request Declined", p_body, "lease", {"lease_request_id": str(lease_request.id)})
    send_email_fallback(tenant.email, "Lease Request Declined", p_body)

# ==========================================
# STANDARD LEASE / RENT PAYMENT HOOKS
# ==========================================

def notify_stk_sent(payment):
    """Alerts a tenant when a standard rent/deposit STK push is requested."""
    try:
        tenant = payment.tenant.user
        p_body = f"An M-Pesa payment request of KES {payment.amount} has been sent to your phone."
        send_push_notification(tenant, "Payment Request", p_body, "payment", {"payment_id": str(payment.id)})
        send_email_fallback(tenant.email, "M-Pesa Payment Request Initiated", p_body)
    except Exception as e:
        print(f"❌ Error in notify_stk_sent: {e}")

def notify_stk_failed(payment):
    """Alerts a tenant when a standard rent/deposit STK push drops or fails."""
    try:
        tenant = payment.tenant.user
        p_body = f"Your payment request of KES {payment.amount} was cancelled or timed out."
        send_push_notification(tenant, "Payment Unsuccessful", p_body, "payment", {"payment_id": str(payment.id)})
        send_email_fallback(tenant.email, "Payment Request Failed", p_body)
    except Exception as e:
        print(f"❌ Error in notify_stk_failed: {e}")

def notify_payment_success(payment):
    """Alerts tenant and landlord upon successful standard wallet/rent settlement."""
    try:
        tenant = payment.tenant.user
        landlord = None
        unit_num = "Unknown"
        
        if payment.lease_request:
            landlord = payment.lease_request.unit.property.landlord.user
            unit_num = payment.lease_request.unit.unit_number
        elif payment.lease:
            landlord = payment.lease.unit.property.landlord.user
            unit_num = payment.lease.unit.unit_number

        t_body = f"We have received your payment of KES {payment.amount}."
        
        try:
            send_push_notification(tenant, "Payment Received", t_body, "payment", {"payment_id": str(payment.id)})
            send_email_fallback(tenant.email, "Payment Confirmed", t_body)
        except Exception as e:
            print(f"Error sending notification to tenant: {e}")
        
        if landlord:
            try:
                tenant_name = tenant.get_full_name() or tenant.email
                l_body = f"{tenant_name} has made a payment of KES {payment.amount} for Unit {unit_num}."
                send_push_notification(landlord, "Payment Collected", l_body, "payment", {"payment_id": str(payment.id)})
                send_email_fallback(landlord.email, "Tenant Payment Received", l_body)
            except Exception as e:
                print(f"Error sending notification to landlord: {e}")
    except Exception as e:
        print(f"❌ Error in notify_payment_success: {e}")

# ==========================================
# MOVE OUT REQUEST HOOKS
# ==========================================

def notify_move_out_request(move_out):
    landlord = move_out.lease.unit.property.landlord.user
    tenant_name = move_out.lease.tenant.user.get_full_name() or move_out.lease.tenant.user.email
    p_body = f"{tenant_name} has requested a move-out for Unit {move_out.lease.unit.unit_number}."
    send_push_notification(landlord, "Move-Out Request", p_body, "move_out", {"move_out_id": str(move_out.id)})
    send_email_fallback(landlord.email, "Notice of Intention to Move Out", p_body)

def notify_move_out_approved(move_out):
    tenant = move_out.lease.tenant.user
    p_body = f"Your move-out request for Unit {move_out.lease.unit.unit_number} has been approved."
    send_push_notification(tenant, "Move-Out Approved", p_body, "move_out", {"move_out_id": str(move_out.id)})
    send_email_fallback(tenant.email, "Move-Out Request Approved", p_body)

def notify_move_out_rejected(move_out):
    tenant = move_out.lease.tenant.user
    p_body = f"Your move-out request was declined. Notes: {move_out.landlord_notes}"
    send_push_notification(tenant, "Move-Out Declined", p_body, "move_out", {"move_out_id": str(move_out.id)})
    send_email_fallback(tenant.email, "Move-Out Request Declined", p_body)

# ==========================================
# EXCLUSIVE LEASE SETTLEMENT TRANSACTION HOOKS
# ==========================================

def notify_settlement_stk_sent(settlement_tx):
    """Alerts a tenant when an STK push is requested explicitly for an outstanding settlement balance."""
    try:
        tenant = settlement_tx.settlement.inspection.move_out_request.lease.tenant.user
        p_body = f"An M-Pesa payment request of KES {settlement_tx.amount} has been sent to your phone for your final settlement."
        payload = {"settlement_id": str(settlement_tx.settlement.id)}
        
        send_push_notification(tenant, "Settlement Payment Requested", p_body, "settlement", payload)
        send_email_fallback(tenant.email, "M-Pesa Settlement Prompt Initiated", p_body)
    except Exception as e:
        print(f"❌ Error in notify_settlement_stk_sent: {e}")

def notify_settlement_stk_failed(settlement_tx):
    """Alerts a tenant when an STK push for a closing settlement fails or times out."""
    try:
        tenant = settlement_tx.settlement.inspection.move_out_request.lease.tenant.user
        p_body = f"Your settlement payment request of KES {settlement_tx.amount} was cancelled or timed out."
        payload = {"settlement_id": str(settlement_tx.settlement.id)}
        
        send_push_notification(tenant, "Settlement Payment Unsuccessful", p_body, "settlement", payload)
        send_email_fallback(tenant.email, "Settlement Payment Failed", p_body)
    except Exception as e:
        print(f"❌ Error in notify_settlement_stk_failed: {e}")

def notify_inspection_completed(inspection, settlement):
    if not inspection.move_out_request or not inspection.move_out_request.lease:
        print("❌ Error: Missing lease relationships for inspection.")
        return

    tenant = inspection.move_out_request.lease.tenant.user
    landlord = inspection.move_out_request.lease.unit.property.landlord.user
    unit_num = inspection.move_out_request.lease.unit.unit_number or "Unknown"
    
    payload = {"settlement_id": str(settlement.id)}
    t_msg = f"Your inspection is complete. Settlement details computed: Balance Owed: KES {settlement.amount_owed}, Refund: KES {settlement.refund_amount}."
    
    try:
        send_push_notification(tenant, "Inspection & Settlement Ready", t_msg, "settlement", payload)
    except Exception as e:
        print(f"⚠️ Tenant push failed: {e}")
        
    try:
        send_email_fallback(tenant.email, "Inspection Completed & Account Summary", t_msg)
    except Exception as e:
        print(f"⚠️ Tenant email failed: {e}")
        
    l_msg = f"Inspection complete for Unit {unit_num}. Settlement sheet generated."
    try:
        send_push_notification(landlord, "Property Inspection Completed", l_msg, "settlement", payload)
    except Exception as e:
        print(f"⚠️ Landlord push failed: {e}")

def notify_settlement_ledger_updated(settlement, ledger_type):
    tenant = settlement.inspection.move_out_request.lease.tenant.user
    landlord = settlement.inspection.move_out_request.lease.unit.property.landlord.user
    
    msg = f"Settlement ledger state updated via manual record: {ledger_type} marked as cleared."
    payload = {"settlement_id": str(settlement.id)}
    
    send_push_notification(tenant, "Settlement Updated", msg, "settlement", payload)
    send_push_notification(landlord, "Settlement Ledger Updated", msg, "settlement", payload)

def notify_settlement_payment_received(settlement):
    tenant = settlement.inspection.move_out_request.lease.tenant.user
    landlord = settlement.inspection.move_out_request.lease.unit.property.landlord.user
    unit_num = settlement.inspection.move_out_request.lease.unit.unit_number
    
    msg = f"Settlement payment of KES {settlement.amount_owed} successfully received for Unit {unit_num}."
    payload = {"settlement_id": str(settlement.id)}
    
    send_push_notification(tenant, "Settlement Payment Confirmed", msg, "settlement", payload)
    send_email_fallback(tenant.email, "Move-Out Balance Cleared", msg)
    
    send_push_notification(landlord, "Settlement Funds Collected", msg, "settlement", payload)
    send_email_fallback(landlord.email, "Tenant Settlement Balance Paid", msg)

def notify_lease_finalized(settlement):
    tenant = settlement.inspection.move_out_request.lease.tenant.user
    landlord = settlement.inspection.move_out_request.lease.unit.property.landlord.user
    p_body = f"Your lease file for Unit {settlement.inspection.move_out_request.lease.unit.unit_number} has been finalized and officially closed."
    payload = {"settlement_id": str(settlement.id)}
    
    send_push_notification(tenant, "Lease File Closed", p_body, "lease", payload)
    send_email_fallback(tenant.email, "Lease File Officially Closed", p_body)
    send_push_notification(landlord, "Lease File Closed", p_body, "lease", payload)

# ==========================================
# MONTHLY BILLING / RECURRING CHARGES HOOKS
# ==========================================

def notify_monthly_billing_and_due_rent(charge):
    lease = charge.lease
    tenant_user = lease.tenant.user
    unit_num = lease.unit.unit_number
    rent_amount = charge.rent_amount
    current_balance = charge.balance

    title = f"🔔 Rent Due & New Month Billed - Unit {unit_num}"
    
    if charge.status == "PAID" or current_balance <= 0:
        body = (
            f"Dear Tenant, a new billing month has commenced. A charge of KES {rent_amount} "
            f"has been applied to Unit {unit_num}. Your available digital wallet credit has automatically "
            f"been applied to fully cover this balance. Thank you!"
        )
    else:
        wallet_deduction_note = ""
        if charge.amount_paid > 0:
            wallet_deduction_note = f"Your wallet credit partially covered KES {charge.amount_paid}. "

        body = (
            f"URGENT NOTICE: A new billing cycle has started, and rent of KES {rent_amount} is due "
            f"for Unit {unit_num}. {wallet_deduction_note}Your outstanding balance is KES {current_balance}. "
            f"Please clear this balance immediately via M-Pesa. Failure to settle rent accounts "
            f"promptly will unfortunately escalate to lease termination and legal eviction proceedings."
        )

    send_push_notification(tenant_user, title, body, "billing", {"lease_id": str(lease.id), "charge_id": str(charge.id)})
    send_email_fallback(tenant_user.email, title, body)

def notify_settlement_stk_sent(settlement_tx):
    """Alerts a tenant when an STK push is requested explicitly for an outstanding settlement balance."""
    try:
        # Safe extraction of nested elements to prevent 500 AttributeErrors
        settlement = getattr(settlement_tx, 'settlement', None)
        if not settlement:
            print("❌ Notification Error: settlement_tx has no linked settlement model.")
            return

        inspection = getattr(settlement, 'inspection', None)
        if not inspection or not inspection.move_out_request:
            print("❌ Notification Error: Settlement is missing an inspection or move_out_request link.")
            return

        tenant = inspection.move_out_request.lease.tenant.user
        p_body = f"An M-Pesa payment request of KES {settlement_tx.amount} has been sent to your phone for your final settlement."
        payload = {"settlement_id": str(settlement.id)}
        
        # 1. Dispatch push notification inside an independent try/catch block
        try:
            print(f"DEBUG: Triggering initiation push to tenant: {tenant.email}")
            send_push_notification(tenant, "Settlement Payment Requested", p_body, "settlement", payload)
        except Exception as push_err:
            print(f"⚠️ Push notification skipped or failed: {push_err}")

        # 2. Dispatch fallback email (This will run even if the push gateway goes down)
        try:
            send_email_fallback(tenant.email, "M-Pesa Settlement Prompt Initiated", p_body)
            print(f"✅ Email successfully queued for {tenant.email}")
        except Exception as email_err:
            print(f"⚠️ Email channel dropped: {email_err}")

    except Exception as e:
        print(f"❌ Core structural crash inside notify_settlement_stk_sent: {e}")


def notify_settlement_stk_failed(settlement_tx):
    """Alerts a tenant when an STK push for a closing settlement fails or times out."""
    try:
        settlement = getattr(settlement_tx, 'settlement', None)
        if not settlement:
            print("❌ Notification Error: settlement_tx has no linked settlement model.")
            return

        inspection = getattr(settlement, 'inspection', None)
        if not inspection or not inspection.move_out_request:
            print("❌ Notification Error: Settlement is missing an inspection or move_out_request link.")
            return

        tenant = inspection.move_out_request.lease.tenant.user
        p_body = f"Your settlement payment request of KES {settlement_tx.amount} was cancelled or timed out."
        payload = {"settlement_id": str(settlement.id)}
        
        # 1. Dispatch push notification inside an independent try/catch block
        try:
            print(f"DEBUG: Triggering failure push to tenant: {tenant.email}")
            send_push_notification(tenant, "Settlement Payment Unsuccessful", p_body, "settlement", payload)
        except Exception as push_err:
            print(f"⚠️ Failure push notification skipped or failed: {push_err}")

        # 2. Dispatch fallback email
        try:
            send_email_fallback(tenant.email, "Settlement Payment Failed", p_body)
            print(f"✅ Failure email successfully queued for {tenant.email}")
        except Exception as email_err:
            print(f"⚠️ Failure email channel dropped: {email_err}")

    except Exception as e:
        print(f"❌ Core structural crash inside notify_settlement_stk_failed: {e}")