import time

from django.core.management.base import BaseCommand

from inventory.services import scan_inventory
from orders.services import release_expired_reservations


class Command(BaseCommand):
    help = "Scan stock and expiry dates, create alerts, and notify staff users."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true", help="Keep scanning continuously.")
        parser.add_argument("--interval", type=int, default=300, help="Seconds between scans.")
        parser.add_argument(
            "--no-notifications", action="store_true", help="Update alerts without email/in-app notices."
        )

    def handle(self, *args, **options):
        interval = max(30, options["interval"])
        while True:
            released_reservations = release_expired_reservations(schedule_scan=False)
            result = scan_inventory(send_notifications=not options["no_notifications"])
            self.stdout.write(
                self.style.SUCCESS(
                    f"Inventory scan complete: {result['active_alerts']} active, "
                    f"{result['new_notifications']} notifications, "
                    f"{released_reservations} expired reservations released."
                )
            )
            if not options["watch"]:
                break
            time.sleep(interval)
