"""Brand-styled AI image prompts (single source of truth for visual_hint enrichment)."""

AI_IMAGE_BRAND_SUFFIX = (
    "\n\n"
    "Styl: rzemieslnicza fotografia kulinarna, naturalne swiatlo, "
    "cieple tony, autentyczna kompozycja, klimat domowej weganskiej "
    "piekarni z Bialegostoku. Square 1:1, 1080x1080, photorealistic, "
    "no text overlay."
)


AI_STORY_BRAND_SUFFIX = (
    "\n\n"
    "Styl: rzemieslnicza fotografia kulinarna, naturalne swiatlo, "
    "cieple tony, autentyczna kompozycja, klimat domowej weganskiej "
    "piekarni z Bialegostoku. Vertical 9:16, 1080x1920, photorealistic, "
    "no text overlay, kompozycja zostawiajaca miejsce na tekst u dolu kadru."
)


def build_ai_image_prompt(visual_hint: str) -> str:
    """Compose final AI prompt: visual_hint + brand suffix."""
    hint = (visual_hint or "").strip()
    return f"{hint}{AI_IMAGE_BRAND_SUFFIX}"


def build_story_image_prompt(visual_hint: str) -> str:
    """Compose vertical (9:16) AI prompt for story backgrounds.

    visual_hint + vertical brand suffix. Empty hint -> suffix only (no crash).
    """
    hint = (visual_hint or "").strip()
    return f"{hint}{AI_STORY_BRAND_SUFFIX}"
