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

        slides = list(wr.story_slides.all())
        if not slides:
            raise CommandError(
                f"WR {wr.week_label}: brak StorySlide — najpierw "
                f"'Promuj stories do StorySlide' w adminie"
            )

        out_dir = (
            Path(settings.MEDIA_ROOT)
            / "weekly_research"
            / wr.week_label
            / "stories"
        )
        renderer = StoryRenderer()

        generated, skipped = 0, 0
        total = len(slides)
        for i, slide in enumerate(slides, start=1):
            slide_type = (
                (slide.slide_type or f"slide{slide.order}")
                .lower()
                .replace(" ", "_")
            )
            filename = f"{slide.order:02d}_{slide_type}.png"
            path = out_dir / filename

            if path.exists() and not force:
                self.stdout.write(self.style.WARNING(f"skip (exists): {path}"))
                skipped += 1
                continue

            renderer.render_to_file(slide, path, index=i, total=total)
            self.stdout.write(self.style.SUCCESS(f"wrote: {path}"))
            generated += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Done {wr.week_label}: generated={generated}, "
                f"skipped={skipped}, total={len(slides)}"
            )
        )
