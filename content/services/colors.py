"""Brand palette helpers (single source of truth)."""

# Hardcoded mapping for brand palette colors.
# Returns the text color that should be used on top of the given background.
BRAND_TEXT_COLOR_MAP = {
    "#2a2420": "#f3ead7",  # ink -> paper
    "#6b7a3a": "#f3ead7",  # olive -> paper
    "#b6562e": "#f3ead7",  # terracotta -> paper
    "#c89a3a": "#2a2420",  # mustard -> ink
    "#f3ead7": "#2a2420",  # paper -> ink
}

DEFAULT_TEXT_COLOR = "#2a2420"


def text_color_for_bg(value: str) -> str:
    """Return readable text color for a given background hex.

    Case-insensitive. Tolerates hex without leading '#'.
    Unknown colors default to ink (#2a2420).
    """
    if not value:
        return DEFAULT_TEXT_COLOR
    key = str(value).strip().lower()
    if not key.startswith("#"):
        key = "#" + key
    return BRAND_TEXT_COLOR_MAP.get(key, DEFAULT_TEXT_COLOR)
