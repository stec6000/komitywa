from django import template

from content.services.colors import text_color_for_bg as _text_color_for_bg

register = template.Library()


@register.filter
def text_color_for_bg(value):
    """Return readable text color for a given background hex (delegate to services.colors)."""
    return _text_color_for_bg(value)


@register.filter
def slide_headline(slide):
    """Return a story slide's headline, tolerating both schemas.

    New schema uses "headline"; legacy slides used "text". Using dict.get
    avoids the VariableDoesNotExist that `{{ s.headline|default:s.text }}`
    raised when a slide had no "text" key (filter args are not
    failure-tolerant). Mirrors the fallback in
    content/admin.py:promote_to_story_slides.
    """
    if not isinstance(slide, dict):
        return ""
    return (slide.get("headline") or slide.get("text") or "").strip()
