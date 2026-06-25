from django.core.management.base import BaseCommand
from django.utils import timezone

from leases.models import Lease
from leases.services import create_monthly_rent_charge

class Command(BaseCommand):

    def handle(self, *args, **kwargs):

        today = timezone.now().date()

        billing_month = today.replace(day=1)

        leases = Lease.objects.filter(
            status="ACTIVE"
        )

        for lease in leases:

            create_monthly_rent_charge(
                lease,
                billing_month
            )

        self.stdout.write(
            self.style.SUCCESS(
                "Rent charges generated."
            )
        )