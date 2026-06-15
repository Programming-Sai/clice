from textual.widgets import Markdown   # Markdown renders .md with tables, bold, code



# ── 4. VerdictMarkdown ────────────────────────────────────────────────────────

class VerdictMarkdown(Markdown):
    """
    The RIGHT hero panel — renders the verdict as real Markdown.

    Textual's built-in Markdown widget handles all the formatting:
    tables, bold, italics, code fences, bullet lists.
    We subclass it purely so we can target it with a CSS selector
    and give it our own colour overrides.

    Subclassing = "copy everything from Markdown, add our own name on top."
    """
    pass   # no extra code needed — the parent Markdown class does all the work

