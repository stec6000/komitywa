"""Generate IG Stories PNGs (1080x1920) for a WeeklyResearch."""

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from content.models import WeeklyResearch
from content.services.story_renderer import StoryRenderer


class Command(BaseCommand):
    help = "Generate Instagram Stories PNGs (1080x1920) for a WeeklyResearch."

    def add_arguments(self, parser):
        parser.add_argument(
            "--week",
            type=str,
            help="WeeklyResearch.week_label (np. 2026-W23)",
        )
        parser.add_argument(
            "--latest",
            action="store_true",
            help="Generate for newest WeeklyResearch with status='formatted'",
        )
        parser.add_argument(
            "--force",
            action="store_true",
            help="Overwrite existing PNGs",
        )

    def handle(self, *args, **opts):
        week = opts.get("week")
        latest = opts.get("latest")
        force = bool(opts.get("force"))

        if bool(week) == bool(latest):
            raise CommandError(
                "Podaj dokladnie jedno z: --week LABEL lub --latest"
            )

        if week:
            try:
                wr = WeeklyResearch.objects.get(week_label=week)
            except WeeklyResearch.DoesNotExist as exc:
                raise CommandError(
                    f"WeeklyResearch o week_label={week!r} nie istnieje"
                ) from exc
        else:
            wr = (
                WeeklyResearch.objects.filter(status="formatted")
                .order_by("-date_to")
                .first()
            )
            if wr is None:
                raise CommandError(
                    "Brak WeeklyResearch ze statusem 'formatted'"
                )

        if not wr.formatted_json:
            raise CommandError(
                f"WR {wr.week_label}: brak formatted_json"
            )

        stories = wr.formatted_json.get("instagram_stories") or []
        if not stories:
            raise CommandError(
                f"WR {wr.week_label}: brak instagram_stories w formatted_json"
            )

        out_dir = (
            Path(settings.MEDIA_ROOT)
            / "weekly_research"
            / wr.week_label
            / "stories"
        )
        renderer = StoryRenderer()

        generated, skipped = 0, 0
        for idx, slide in enumerate(stories):
            slide_type = (
                (slide.get("slide_type") or f"slide{idx + 1}")
                .lower()
                .replace(" ", "_")
            )
            filename = f"{idx + 1:02d}_{slide_type}.png"
            path = out_dir / filename

            if path.exists() and not force:
                self.stdout.write(self.style.WARNING(f"skip (exists): {path}"))
                skipped += 1
                continue

            renderer.render_to_file(slide, path)
            self.stdout.write(self.style.SUCCESS(f"wrote: {path}"))
            generated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done {wr.week_label}: generated={generated}, "
                f"skipped={skipped}, total={len(stories)}"
            )
        )
