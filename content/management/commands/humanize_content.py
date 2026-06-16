"""Backfill: czyszczenie typografii w juz zapisanym contencie.

Stosuje deterministyczny sanitizer (content/services/humanize.py) do istniejacych
wierszy WeeklyResearch / BlogPost / StorySlide. Tryb --dry-run pokazuje co BY sie
zmienilo, bez zapisu. Zapis dotyka WYLACZNIE realnie zmienionych pol (update_fields).
"""

from django.core.management.base import BaseCommand

from content.models import WeeklyResearch, BlogPost, StorySlide
from content.services.humanize import humanize_text, humanize_json


def _truncate(value, limit=120):
    text = repr(value)
    if len(text) > limit:
        return text[:limit] + "..."
    return text


class Command(BaseCommand):
    help = "Czysci typografie (mysliki, wielokropek, cudzyslowy) w zapisanym contencie."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Pokaz co BY sie zmienilo, bez zapisu.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        prefix = "[DRY-RUN] " if dry_run else ""

        self._handle_weekly_research(dry_run, prefix)
        self._handle_blog_posts(dry_run, prefix)
        self._handle_story_slides(dry_run, prefix)

    def _handle_weekly_research(self, dry_run, prefix):
        changed = 0
        samples = []
        for row in WeeklyResearch.objects.all():
            if row.formatted_json is None:
                continue
            cleaned = humanize_json(row.formatted_json)
            if cleaned == row.formatted_json:
                continue
            changed += 1
            if len(samples) < 3:
                samples.append((row.pk, row.formatted_json, cleaned))
            if not dry_run:
                row.formatted_json = cleaned
                row.save(update_fields=["formatted_json", "updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}WeeklyResearch: {changed} wierszy do zmiany."
            )
        )
        if dry_run:
            for pk, before, after in samples:
                self.stdout.write(
                    f"  - #{pk}: {_truncate(before)} -> {_truncate(after)}"
                )

    def _handle_blog_posts(self, dry_run, prefix):
        changed = 0
        samples = []
        for row in BlogPost.objects.all():
            update_fields = []
            first_diff = None
            for field in ("title", "excerpt", "body"):
                current = getattr(row, field)
                cleaned = humanize_text(current)
                if cleaned != current:
                    setattr(row, field, cleaned)
                    update_fields.append(field)
                    if first_diff is None:
                        first_diff = (field, current, cleaned)
            if not update_fields:
                continue
            changed += 1
            if len(samples) < 3 and first_diff is not None:
                samples.append((row.pk, *first_diff))
            if not dry_run:
                row.save(update_fields=update_fields + ["updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}BlogPost: {changed} wierszy do zmiany (pole tags pominiete)."
            )
        )
        if dry_run:
            for pk, field, before, after in samples:
                self.stdout.write(
                    f"  - #{pk}.{field}: {_truncate(before)} -> {_truncate(after)}"
                )

    def _handle_story_slides(self, dry_run, prefix):
        changed = 0
        samples = []
        for row in StorySlide.objects.all():
            update_fields = []
            first_diff = None
            for field in ("headline", "subtext", "visual_hint"):
                current = getattr(row, field)
                cleaned = humanize_text(current)
                if cleaned != current:
                    setattr(row, field, cleaned)
                    update_fields.append(field)
                    if first_diff is None:
                        first_diff = (field, current, cleaned)
            if not update_fields:
                continue
            changed += 1
            if len(samples) < 3 and first_diff is not None:
                samples.append((row.pk, *first_diff))
            if not dry_run:
                row.save(update_fields=update_fields + ["updated_at"])

        self.stdout.write(
            self.style.SUCCESS(
                f"{prefix}StorySlide: {changed} wierszy do zmiany."
            )
        )
        if dry_run:
            for pk, field, before, after in samples:
                self.stdout.write(
                    f"  - #{pk}.{field}: {_truncate(before)} -> {_truncate(after)}"
                )
