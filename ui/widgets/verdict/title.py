from textual.widgets import Static
from rich.text import Text

from ui.widgets.utils.design import ACCENT_ERR, ACCENT_OK, ACCENT_WARN


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

ERROR_ART = """\
 ███████╗██████╗ ██████╗  ██████╗ ██████╗ 
 ██╔════╝██╔══██╗██╔══██╗██╔═══██╗██╔══██╗
 █████╗  ██████╔╝██████╔╝██║   ██║██████╔╝
 ██╔══╝  ██╔══██╗██╔══██╗██║   ██║██╔══██╗
 ███████╗██║  ██║██║  ██║╚██████╔╝██║  ██║
 ╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝"""


# ── 1. BigTitle ───────────────────────────────────────────────────────────────

class BigTitle(Static):
    """The huge ASCII-art PASS / FAIL / ERROR at the top of the screen.

    verdict_state is one of "pass", "fail", "error":
      - "pass"  → the checker ran and the user met the objective
      - "fail"  → the checker ran and the user did NOT meet the objective
      - "error" → the checker never produced a real verdict at all
                  (missing interpreter, timeout, couldn't stage the script) -
                  this is NOT the same as failing the challenge, so it gets
                  its own distinct amber banner rather than lumping in with FAIL.
    """

    def __init__(self, verdict_state: str = "fail", **kwargs):
        super().__init__(**kwargs)
        self.verdict_state = verdict_state
        self.art = {
            "pass": PASS_ART,
            "fail": FAIL_ART,
            "error": ERROR_ART,
        }.get(verdict_state, FAIL_ART)
        self.color = {
            "pass": ACCENT_OK,
            "fail": ACCENT_ERR,
            "error": ACCENT_WARN,
        }.get(verdict_state, ACCENT_ERR)

    def render(self) -> Text:
        t = Text(justify="center")    # centre every line horizontally
        for line in self.art.splitlines():
            t.append(line + "\n", style=f"bold {self.color}")
        return t