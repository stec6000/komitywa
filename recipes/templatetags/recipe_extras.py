from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe


register = template.Library()


@register.filter
def format_ingredients(text):
    """Render ingredients_text as a styled list.

    Lines ending with ":" are treated as group headers (class
    ``kk-ingredient-group``); all other non-empty lines are items
    (class ``kk-ingredient-item``). Every line is HTML-escaped before
    insertion to guard against XSS from admin-editable content.
    """
    if not text:
        return ""

    items = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        safe_line = escape(line)
        if line.endswith(":"):
            css_class = "kk-ingredient-group"
        else:
            css_class = "kk-ingredient-item"
        items.append(f'<li class="{css_class}">{safe_line}</li>')

    if not items:
        return ""

    return mark_safe(
        '<ul class="kk-ingredient-list">' + "".join(items) + "</ul>"
    )
