import secrets


def generate_entry_code():

    return secrets.token_hex(
        4
    ).upper()

from .models import LeaseWallet


def create_lease_wallet(
    lease
):

    return LeaseWallet.objects.create(
        lease=lease
    )