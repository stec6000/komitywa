from django import template

register = template.Library()


# Hardcoded mapping for brand palette colors.
# Returns the text color that should be used on top of the given background.
_BRAND_TEXT_COLOR_MAP = {
    "#2a2420": "#f3ead7",  # ink → paper (jasny tekst)
    "#6b7a3a": "#f3ead7",  # olive → paper
    "#b6562e": "#f3ead7",  # terracotta → paper
    "#c89a3a": "#2a2420",  # mustard → ink (żółty wymaga ciemnego tekstu)
    "#f3ead7": "#2a2420",  # paper → ink
}

_DEFAULT_TEXT_COLOR = "#2a2420"


@register.filter
def text_color_for_bg(value):
    """Return readable text color for a given background hex.

    Case-insensitive. Unknown colors default to ink (#2a2420).
    """
    if not value:
        return _DEFAULT_TEXT_COLOR
    key = str(value).strip().lower()
    return _BRAND_TEXT_COLOR_MAP.get(key, _DEFAULT_TEXT_COLOR)
