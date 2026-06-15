from textual.widgets import Static
from rich.text import Text

from ui.widgets.utils.design import ACCENT_ERR, ACCENT_OK


# ══════════════════════════════════════════════════════════════════════════════
#  🔤 ASCII ART TITLES
# ══════════════════════════════════════════════════════════════════════════════

PASS_ART = """\
 ██████╗  █████╗ ███████╗███████╗
 ██╔══██╗██╔══██╗██╔════╝██╔════╝
 ██████╔╝███████║███████╗███████╗ 
 ██╔═══╝ ██╔══██║╚════██║╚════██║
 ██║     ██║  ██║███████║███████║
 ╚═╝     ╚═╝  ╚═╝╚══════╝╚══════╝"""

FAIL_ART = """\
 ███████╗ █████╗ ██╗██╗     
 ██╔════╝██╔══██╗██║██║     
 █████╗  ███████║██║██║     
 ██╔══╝  ██╔══██║██║██║     
 ██║     ██║  ██║██║███████╗
 ╚═╝     ╚═╝  ╚═╝╚═╝╚══════╝"""





# ── 1. BigTitle ───────────────────────────────────────────────────────────────

class BigTitle(Static):
    """The huge ASCII-art PASS / FAIL at the top of the screen."""

    def __init__(self, is_passing: bool, **kwargs):
        super().__init__(**kwargs)
        self.is_passing = is_passing
        self.art = PASS_ART if is_passing else FAIL_ART
        self.color = ACCENT_OK if is_passing else ACCENT_ERR

    def render(self) -> Text:
        t = Text(justify="center")    # centre every line horizontally
        for line in self.art.splitlines():
            t.append(line + "\n", style=f"bold {self.color}")
        return t

