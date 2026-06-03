from django import template

from content.services.colors import text_color_for_bg as _text_color_for_bg

register = template.Library()


@register.filter
def text_color_for_bg(value):
    """Return readable text color for a given background hex (delegate to services.colors)."""
    return _text_color_for_bg(value)
