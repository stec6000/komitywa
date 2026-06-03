import datetime as dt

from django.core.management.base import BaseCommand, CommandError

from newsletter.models import Subscriber


DEFAULT_SINCE = "2026-05-09"


class Command(BaseCommand):
    help = (
        "Usuwa junk subskrybentów newslettera (głównie boty) utworzonych "
        "od podanej daty. Domyślnie usuwa tylko niepotwierdzonych."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--since",
            default=DEFAULT_SINCE,
            help=f"Data od kiedy (YYYY-MM-DD). Domyślnie {DEFAULT_SINCE}.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Pokaż co byłoby usunięte, nie usuwaj nic.",
        )
        parser.add_argument(
            "--include-confirmed",
            action="store_true",
            help="Usuń też potwierdzonych subskrybentów (domyślnie tylko unconfirmed).",
        )
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Pomiń interaktywne potwierdzenie (wymagane gdy NIE --dry-run).",
        )

    def handle(self, *args, **options):
        since_str = options["since"]
        try:
            since = dt.date.fromisoformat(since_str)
        except ValueError as exc:
            raise CommandError(f"Nieprawidłowa data --since: {since_str} ({exc})")

        dry_run = options["dry_run"]
        include_confirmed = options["include_confirmed"]
        skip_prompt = options["yes"]

        qs = Subscriber.objects.filter(created_at__date__gte=since)

        total = qs.count()
        unconfirmed = qs.filter(is_confirmed=False).count()
        confirmed = qs.filter(is_confirmed=True).count()
        unsubscribed = qs.filter(is_unsubscribed=True).count()

        targets = qs if include_confirmed else qs.filter(is_confirmed=False)
        target_count = targets.count()

        self.stdout.write(f"\nSubskrybenci od {since}:")
        self.stdout.write(f"  Total           : {total}")
        self.stdout.write(f"  Unconfirmed     : {unconfirmed}{'  <- usuniemy' if not include_confirmed else ''}")
        self.stdout.write(f"  Confirmed       : {confirmed}{'  <- usuniemy' if include_confirmed else ''}")
        self.stdout.write(f"  Unsubscribed    : {unsubscribed}")
        self.stdout.write("")
        self.stdout.write(
            self.style.WARNING(
                f"Do usunięcia: {target_count} rekordów "
                f"({'wszystkich' if include_confirmed else 'tylko unconfirmed'})"
            )
        )

        sample_emails = list(
            targets.values_list("email", flat=True).order_by("email")[:10]
        )
        if sample_emails:
            self.stdout.write("\nPróbka pierwszych 10 emaili do usunięcia:")
            for email in sample_emails:
                self.stdout.write(f"  - {email}")

        if dry_run:
            self.stdout.write(
                "\n" + self.style.SUCCESS("DRY RUN — nic nie usunięto. "
                "Dodaj --yes (bez --dry-run) żeby faktycznie usunąć.")
            )
            return

        if target_count == 0:
            self.stdout.write(self.style.SUCCESS("\nBrak rekordów do usunięcia."))
            return

        if not skip_prompt:
            self.stdout.write("")
            answer = input(f"Wpisz 'yes' żeby usunąć {target_count} rekordów: ")
            if answer.strip().lower() != "yes":
                self.stdout.write(self.style.WARNING("Anulowano."))
                return

        deleted_count, _ = targets.delete()
        self.stdout.write(
            self.style.SUCCESS(f"\nUsunięto {deleted_count} rekordów.")
        )
