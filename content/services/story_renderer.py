"""PNG renderer for Instagram Stories (1080x1920) — uses bundled Noto Sans fonts."""

from __future__ import annotations

import textwrap
from io import BytesIO
from pathlib import Path
from typing import Optional

from PIL import Image, ImageDraw, ImageFont

from content.services.colors import text_color_for_bg

FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"


class StoryRenderer:
    CANVAS_SIZE = (1080, 1920)
    FONT_PATH_REGULAR = FONTS_DIR / "NotoSans-Regular.ttf"
    FONT_PATH_BOLD = FONTS_DIR / "NotoSans-Bold.ttf"
    FONT_PATH_EMOJI = FONTS_DIR / "NotoColorEmoji.ttf"

    EMOJI_SIZE = 240
    EMOJI_Y = 320
    TEXT_SIZE = 80
    TEXT_Y_TOP = 720
    TEXT_LINE_HEIGHT = 100
    TEXT_MAX_CHARS_PER_LINE = 14
    LABEL_SIZE = 36
    LABEL_Y = 1760

    def __init__(self) -> None:
        if not self.FONT_PATH_REGULAR.exists() or not self.FONT_PATH_BOLD.exists():
            raise RuntimeError(
                f"Required fonts missing in {FONTS_DIR}: NotoSans-Regular.ttf and NotoSans-Bold.ttf"
            )
        self._font_regular = ImageFont.truetype(str(self.FONT_PATH_REGULAR), self.LABEL_SIZE)
        self._font_bold = ImageFont.truetype(str(self.FONT_PATH_BOLD), self.TEXT_SIZE)
        self._font_emoji: Optional[ImageFont.FreeTypeFont] = None
        if self.FONT_PATH_EMOJI.exists():
            try:
                # NotoColorEmoji is a bitmap font with fixed size (typically 109).
                self._font_emoji = ImageFont.truetype(str(self.FONT_PATH_EMOJI), 109)
            except Exception:
                self._font_emoji = None

    @staticmethod
    def _parse_hex(color: str, default: str = "#f3ead7") -> tuple:
        value = (color or default).strip().lstrip("#")
        if len(value) != 6:
            value = default.lstrip("#")
        try:
            return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))
        except ValueError:
            value = default.lstrip("#")
            return tuple(int(value[i : i + 2], 16) for i in (0, 2, 4))

    def render(self, slide: dict) -> bytes:
        bg_hex = slide.get("bg_color") or "#f3ead7"
        bg_rgb = self._parse_hex(bg_hex)
        text_color_hex = text_color_for_bg(bg_hex)
        text_rgb = self._parse_hex(text_color_hex, default="#2a2420")

        img = Image.new("RGB", self.CANVAS_SIZE, bg_rgb)
        draw = ImageDraw.Draw(img)
        canvas_w, _ = self.CANVAS_SIZE

        # ---- Emoji (top, centered) ----
        emoji = (slide.get("emoji") or "").strip()
        if emoji:
            rendered = False
            if self._font_emoji is not None:
                try:
                    bbox = draw.textbbox((0, 0), emoji, font=self._font_emoji, embedded_color=True)
                    ew = bbox[2] - bbox[0]
                    draw.text(
                        ((canvas_w - ew) // 2, self.EMOJI_Y),
                        emoji,
                        font=self._font_emoji,
                        embedded_color=True,
                    )
                    rendered = True
                except Exception:
                    rendered = False
            if not rendered:
                fallback_font = ImageFont.truetype(str(self.FONT_PATH_BOLD), self.EMOJI_SIZE)
                bbox = draw.textbbox((0, 0), emoji, font=fallback_font)
                ew = bbox[2] - bbox[0]
                draw.text(
                    ((canvas_w - ew) // 2, self.EMOJI_Y),
                    emoji,
                    font=fallback_font,
                    fill=text_rgb,
                )

        # ---- Main text (auto-wrap, centered) ----
        text = (slide.get("text") or "").strip()
        if text:
            lines = textwrap.wrap(text, width=self.TEXT_MAX_CHARS_PER_LINE) or [text]
            y = self.TEXT_Y_TOP
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=self._font_bold)
                lw = bbox[2] - bbox[0]
                draw.text(
                    ((canvas_w - lw) // 2, y),
                    line,
                    font=self._font_bold,
                    fill=text_rgb,
                )
                y += self.TEXT_LINE_HEIGHT

        # ---- Label (bottom, uppercase, letter-spaced, dimmed) ----
        label = (slide.get("slide_type") or "").upper()
        if label:
            spaced = " ".join(list(label))
            bbox = draw.textbbox((0, 0), spaced, font=self._font_regular)
            lw = bbox[2] - bbox[0]
            # simulate 70% opacity by blending text color toward bg
            r = int(text_rgb[0] * 0.7 + bg_rgb[0] * 0.3)
            g = int(text_rgb[1] * 0.7 + bg_rgb[1] * 0.3)
            b = int(text_rgb[2] * 0.7 + bg_rgb[2] * 0.3)
            draw.text(
                ((canvas_w - lw) // 2, self.LABEL_Y),
                spaced,
                font=self._font_regular,
                fill=(r, g, b),
            )

        buf = BytesIO()
        img.save(buf, format="PNG", optimize=True)
        return buf.getvalue()

    def render_to_file(self, slide: dict, path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(self.render(slide))
        return path
