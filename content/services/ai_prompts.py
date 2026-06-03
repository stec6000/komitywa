"""Brand-styled AI image prompts (single source of truth for visual_hint enrichment)."""

AI_IMAGE_BRAND_SUFFIX = (
    "\n\n"
    "Styl: rzemieslnicza fotografia kulinarna, naturalne swiatlo, "
    "cieple tony, autentyczna kompozycja, klimat domowej weganskiej "
    "piekarni z Bialegostoku. Square 1:1, 1080x1080, photorealistic, "
    "no text overlay."
)


def build_ai_image_prompt(visual_hint: str) -> str:
    """Compose final AI prompt: visual_hint + brand suffix."""
    hint = (visual_hint or "").strip()
    return f"{hint}{AI_IMAGE_BRAND_SUFFIX}"
