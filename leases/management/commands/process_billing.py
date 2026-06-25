from django.core.management.base import BaseCommand

from leases.services import generate_due_rent_charges


class Command(BaseCommand):

    def handle(self, *args, **kwargs):
        generate_due_rent_charges()

        self.stdout.write(
            self.style.SUCCESS("Billing processed")
        )