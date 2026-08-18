from django.core.management.base import BaseCommand

from shop.reservations import (
    delete_old_inactive_reservations,
    expire_due_reservations,
)


class Command(BaseCommand):
    help = "Wygasza przeterminowane Rezerwacje Rzutu i zwalnia ich Pulę."

    def handle(self, *args, **options):
        expired_count = expire_due_reservations()
        deleted_count = delete_old_inactive_reservations()
        self.stdout.write(f"Wygaszono Rezerwacje: {expired_count}")
        self.stdout.write(f"Usunięto stare Rezerwacje: {deleted_count}")
