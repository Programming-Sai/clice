from textual.widgets import Static
from rich.text import Text

from ui.widgets.utils.design import BRAND


# ── 6. EOFMarker ──────────────────────────────────────────────────────────────

class EOFMarker(Static):
    """--- EOF: LOG SESSION 8291 ---   signals end of log."""

    def render(self) -> Text:
        t = Text()
        t.append("--- EOF: LOG SESSION 8291 ---", style=BRAND)
        return t

