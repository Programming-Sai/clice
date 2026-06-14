"""
verdict_screen.py
==============
Layout priority:
  1. SYSTEM_VERDICT  — the big story (right, 62%, tall hero row)
  2. METRICS         — the numbers + challenge metadata (left, 38%, same hero row)
  3. TIMELINE        — the raw log (slim strip at the bottom, always visible)

The challenge info panel is GONE. Its metadata now lives inside MetricsPanel
so the eye never has to leave the two primary panels to find context.

HOW TEXTUAL WORKS (quick refresher):
-------------------------------------
1. App       = the whole toy box. One per program.
2. compose() = where we snap widgets onto the screen.
3. Widgets   = individual pieces (labels, boxes, markdown views …).
4. CSS       = paint + ruler controlling colours, sizes, positions.
5. reactive  = a magic variable that redraws the screen when it changes.

To install:
    pip install textual

To run:
    python pass_screen.py

Dev mode (live CSS inspector — very useful!):
    textual run --dev pass_screen.py
"""

# ── Imports ────────────────────────────────────────────────────────────────────

from textual.app import App, ComposeResult
from textual.widgets import Static, Markdown   # Markdown renders .md with tables, bold, code
from textual.containers import (
    Horizontal,          # side by side: LEFT ↔ RIGHT
    Vertical,            # stacked: UP ↕ DOWN
    ScrollableContainer, # a box you can scroll inside
)
from textual.reactive import reactive          # magic variable → auto-redraws on change
from rich.text import Text

from ui.screens.data.challenges import CHALLENGES                     # Rich Text = coloured / styled terminal text


# ══════════════════════════════════════════════════════════════════════════════
#  🚦 MASTER SWITCH  —  flip this one bool to change everything
# ══════════════════════════════════════════════════════════════════════════════
#
#   IS_PASSING = True   →  teal/green theme,  big ASCII "PASS" title
#   IS_PASSING = False  →  teal/red  theme,   big ASCII "FAIL" title

# IS_PASSING: bool = True   # ← change to False to see the FAIL screen
IS_PASSING: bool = False   # ← change to True to see the FAIL screen


# ══════════════════════════════════════════════════════════════════════════════
#  🎨 COLOUR PALETTE
# ══════════════════════════════════════════════════════════════════════════════
#
# Giving colours friendly names means we only change a hex code in ONE place
# and it updates everywhere on the screen automatically.

BRAND      = "#00e5cc"   # main teal  — borders, section headers, timestamps
ACCENT_OK  = "#00ff88"   # bright green — scores, exit codes on PASS
ACCENT_ERR = "#ff3c3c"   # bright red   — scores, exit codes on FAIL
DIM_BRAND  = "#005c54"   # dark teal    — muted separators, dim borders
BG         = "#0a0f0e"   # near-black background
TEXT       = "#c8fff9"   # soft off-white — main readable body text
DIM_TEXT   = "#4a8f88"   # dim teal-grey  — labels, secondary info

# Pick the live accent based on the master switch.
# Python ternary syntax:  value_if_true  if  condition  else  value_if_false
ACCENT = ACCENT_OK if IS_PASSING else ACCENT_ERR

def get_difficulty_color(difficulty):
    if difficulty == "beginner":
        return '#00ff88'
    elif difficulty == "intermediate":
        return '#ff9900'
    elif difficulty == "advanced":
        return '#ff3333'

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

TITLE_ART   = PASS_ART if IS_PASSING else FAIL_ART
TITLE_COLOR = ACCENT_OK if IS_PASSING else ACCENT_ERR


# ══════════════════════════════════════════════════════════════════════════════
#  📋 CHALLENGE DATA
# ══════════════════════════════════════════════════════════════════════════════
#
# One dict per challenge. Swap this out (or load from JSON/YAML) to power
# different challenges without changing any widget code.

CHALLENGE = CHALLENGES[0]


# ══════════════════════════════════════════════════════════════════════════════
#  📝 VERDICT MARKDOWN  —  one string per scenario
# ══════════════════════════════════════════════════════════════════════════════
#
# VERDICT_MD_PASS  shown when IS_PASSING = True  (green screen)
# VERDICT_MD_FAIL  shown when IS_PASSING = False (red screen)
#
# These are full Markdown strings. Textual's Markdown widget renders them with
# real formatting: bold, italics, tables, code fences, bullet lists.

VERDICT_MD_PASS = """\
## ✅ Session Validated

All environment assertions returned **EXIT_CODE(0)**. The submission adheres
to the structural integrity constraints defined in `CLICE_CORE_v4.2`.
Optimization thresholds were met with a **12 % margin**.

### What You Demonstrated

- Correct octal permission bits on `/etc/shadow` (`640`)
- Recursive ownership change on the web root using `find … -exec`
- `umask 027` configured for the shared group directory with `g+s`

### Score Breakdown

| Check | Result |
|-------|--------|
| `/etc/shadow` permissions | ✅ PASS |
| Web root ownership | ✅ PASS |
| umask + setgid bit | ✅ PASS |

> **Next challenge:** `CH-02 — SUDOERS_HARDENING`
"""

VERDICT_MD_FAIL = """\
## ❌ Session Failed

One or more environment assertions returned **EXIT_CODE(1)**. Review the
failed checks below and resubmit.

### Failed Checks

| Check | Result | Hint |
|-------|--------|------|
| `/etc/shadow` permissions | ❌ FAIL | Expected `640`, got `644` — world-readable! |
| Web root ownership | ❌ FAIL | `chown -R` used directly; use `find … -exec` |
| umask + setgid bit | ✅ PASS | — |

### Reminder: Core Concepts

`chmod` octal digit = **4** (read) + **2** (write) + **1** (execute).

```bash
chmod 640 /etc/shadow
find /var/www -exec chown www-data:www-data {} +
```

> Re-run `./scripts/validate_integrity.sh` after each fix.
"""

# The one we'll actually render, chosen by the master switch
ACTIVE_VERDICT_MD = VERDICT_MD_PASS if IS_PASSING else VERDICT_MD_FAIL


# ── Timeline log rows ─────────────────────────────────────────────────────────
# Each tuple: (timestamp, command, exit_code_string)

TIMELINE_ROWS = [
    ("[14:20:01]", "systemctl status clice-daemon",         f"({'0' if IS_PASSING else '1'})"),
    ("[14:20:15]", "ls -la /var/log/clice/",                f"({'0' if IS_PASSING else '1'})"),
    ("[14:20:45]", "sed -i 's/DEBUG/INFO/g' config.yaml",   f"({'0' if IS_PASSING else '1'})"),
    ("[14:21:10]", 'grep -r "CRITICAL" ./src',              f"({'0' if IS_PASSING else '1'})"),
    ("[14:22:05]", "./scripts/validate_integrity.sh",       f"({'0' if IS_PASSING else '1'})"),
    ("[14:23:30]", "curl -X POST localhost:8080/v1/submit",  f"({'0' if IS_PASSING else '1'})"),
    ("[14:24:00]", "rm -rf ./tmp/*",                        f"({'0' if IS_PASSING else '1'})"),
    ("[14:24:12]", 'echo "SUBMISSION_COMPLETE"',             f"({'0' if IS_PASSING else '1'})"),
]


# ══════════════════════════════════════════════════════════════════════════════
#  🧱 WIDGETS
# ══════════════════════════════════════════════════════════════════════════════
#
# Each widget is a small class that knows how to draw itself.
# We inherit from Static (the simplest Textual widget) and override render()
# to return a Rich Text object with colours and styles applied.


# ── 1. BigTitle ───────────────────────────────────────────────────────────────

class BigTitle(Static):
    """The huge ASCII-art PASS / FAIL at the top of the screen."""

    def render(self) -> Text:
        t = Text(justify="center")    # centre every line horizontally
        for line in TITLE_ART.splitlines():
            t.append(line + "\n", style=f"bold {TITLE_COLOR}")
        return t


# ── 2. SectionHeader ──────────────────────────────────────────────────────────

class SectionHeader(Static):
    """▌▌ PANEL_NAME ▌▌  — the small label bar at the top of each box."""

    def __init__(self, title: str, **kwargs):
        super().__init__(**kwargs)   # always forward **kwargs to the parent
        self._title = title

    def render(self) -> Text:
        t = Text()
        t.append("▌▌ ", style=BRAND)
        t.append(self._title, style=f"bold {TEXT}")
        t.append(" ▌▌", style=BRAND)
        return t


# ── 3. MetricsPanel ───────────────────────────────────────────────────────────

class MetricsPanel(Static):
    """
    The LEFT hero panel.

    Shows two things in one place:
      A) Challenge metadata  (id, category, difficulty, tags, objectives)
      B) Run metrics         (commands, time, error rate, score, progress bar)

    Putting both here means the player's eye never needs to hunt for context —
    it's all in the same box as the numbers.

    All metric values are reactive: changing them anywhere in the program
    will automatically trigger a redraw of just this widget.
    """

    # ── reactive metric values ────────────────────────────────────────────────
    # reactive() = "watch this; redraw if it changes".
    # Think of a scoreboard at a basketball game: the number changes live.
    total_commands: reactive[int]   = reactive(42)
    time_elapsed:   reactive[str]   = reactive("00:12:44")
    correctness:     reactive[float] = reactive(72.00 if IS_PASSING else 0.00)
    error_rate:     reactive[float] = reactive(0.00 if IS_PASSING else 75.00)
    score:          reactive[str]   = reactive(f"{'98' if IS_PASSING else '12'}/100")
    probability:    reactive[int]   = reactive(98 if IS_PASSING else 12)

    def render(self) -> Text:
        t = Text()
        c = CHALLENGE   # short alias

        # ══ A. CHALLENGE METADATA ════════════════════════════════════════════

        t.append("\n")

        # ID + title on the same line — ID is dim, title is bright
        t.append(f" {c['id']}  ", style=f"dim {BRAND}")
        t.append(c["title"] + "\n", style=f"bold {BRAND}")

        t.append(" " + "─" * 32 + "\n", style=DIM_BRAND)

        # Category and difficulty as a two-column mini-table.
        # f"{label:<12}" pads to 12 chars so the values line up.
        t.append(f" {'CATEGORY':<12}", style=DIM_TEXT)
        t.append(c["category"] + "\n", style=TEXT)

        t.append(f" {'DIFFICULTY':<12}", style=DIM_TEXT)
        t.append(c["difficulty"] + "\n", style=get_difficulty_color(c["difficulty"].split(" [")[0].lower()))
        
        # Tags as little coloured chips  [ CHMOD ] [ CHOWN ] …
        t.append(f" {'TAGS':<12}", style=DIM_TEXT)
        for tag in c["tags"]:
            # "bold black on COLOR" = dark letters printed on a coloured background
            t.append(f" {tag} ", style=f"bold black on {BRAND}")
            t.append(" ")
        t.append("\n")

        t.append(" " + "─" * 32 + "\n", style=DIM_BRAND)

        # Objectives — short bullet list
        t.append(" OBJECTIVES\n", style=DIM_TEXT)
        for obj in c["objectives"]:
            t.append("  ▸ ", style=BRAND)
            t.append(obj + "\n", style=TEXT)

        t.append(" " + "─" * 32 + "\n", style=DIM_BRAND)

        # ══ B. RUN METRICS ═══════════════════════════════════════════════════

        # Helper: print one  LABEL:          VALUE  line
        # The label is dim so your eye jumps straight to the value.
        def row(label: str, value: str, value_style: str = ACCENT) -> None:
            t.append(f" {label:<20}", style=DIM_TEXT)
            t.append(f"{value}\n",   style=value_style)

        t.append("\n")
        row("TOTAL COMMANDS:", str(self.total_commands))
        row("TIME ELAPSED:",   self.time_elapsed, BRAND)
        row("CORRECTNESS (%):", f"{self.correctness:.2f}%")
        row("ERROR RATE (%):", f"{self.error_rate:.2f}%")

        t.append(" " + "─" * 32 + "\n", style=DIM_BRAND)

        row("SCORE:", self.score)

        # ── PROBABILITY_MAP bar ───────────────────────────────────────────────
        # Visual progress bar:  [████████        ] 50%
        # █ = filled,  space = empty
        bar_width = 18
        filled    = int(bar_width * self.probability / 100)
        empty     = bar_width - filled

        t.append("\n PROBABILITY_MAP\n ", style=DIM_TEXT)
        t.append("[",             style=DIM_BRAND)
        t.append("█" * filled,   style=ACCENT)
        t.append(" " * empty,    style=DIM_BRAND)
        t.append("] ",           style=DIM_BRAND)
        t.append(f"{self.probability}%", style=ACCENT)

        return t


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


# ── 5. TimelineRow ────────────────────────────────────────────────────────────

class TimelineRow(Static):
    """One log line:  [14:20:01] ▌ command text…                    (0)"""

    def __init__(self, timestamp: str, command: str, exit_code: str, **kwargs):
        super().__init__(**kwargs)
        self._timestamp = timestamp
        self._command   = command
        self._exit_code = exit_code

    def render(self) -> Text:
        t = Text()
        t.append(self._timestamp + " ", style=f"dim {BRAND}")   # faded timestamp
        t.append("▌ ",                  style=BRAND)             # decorative bar
        t.append(f"{self._command:<52}", style=TEXT)             # command, padded
        t.append(self._exit_code,        style=ACCENT)           # (0) or (1)
        return t


# ── 6. EOFMarker ──────────────────────────────────────────────────────────────

class EOFMarker(Static):
    """--- EOF: LOG SESSION 8291 ---   signals end of log."""

    def render(self) -> Text:
        t = Text()
        t.append("--- EOF: LOG SESSION 8291 ---", style=BRAND)
        return t


# ══════════════════════════════════════════════════════════════════════════════
#  📦 THE APP
# ══════════════════════════════════════════════════════════════════════════════

class VerdictScreen(App):
    """
    The main Textual application — the whole toy box.

    FINAL LAYOUT (top → bottom):
    ┌──────────── BigTitle (ASCII art PASS / FAIL) ──────────────┐
    │                                                             │
    ├─ #hero-row (Horizontal, takes most of the vertical space) ─┤
    │  ┌─ #metrics-box (38%) ──┐  ┌─ #verdict-box (62%) ───────┐ │
    │  │  challenge metadata   │  │  markdown verdict           │ │
    │  │  ─────────────────    │  │  (scrollable)               │ │
    │  │  run metrics          │  │                             │ │
    │  └───────────────────────┘  └─────────────────────────────┘ │
    │                                                             │
    ├─ #timeline-box (slim strip, scrollable) ────────────────── ┤
    │  log rows …                                                 │
    └─────────────────────────────────────────────────────────────┘
    └─ footer bar (docked to very bottom) ───────────────────────┘

    The hero-row gets "height: 1fr" which means:
      "stretch me to fill whatever vertical space is left after
       the title, timeline, and footer have taken their fixed share."
    This makes the two most important panels as tall as possible.
    """

    CSS = f"""
    /* ── Global background & default text colour ── */
    Screen {{
        background: {BG};
        color: {TEXT};
    }}

    /* ── Outer wrapper: one tall column ── */
    #root-container {{
        width: 100%;
        height: 100%;
        padding: 1 2;
    }}

    /* ── ASCII art title ── */
    BigTitle {{
        width: 100%;
        content-align: center middle;
        height: 8;
        margin-bottom: 1;
    }}

    /* ── HERO ROW: the two primary panels side by side ──────────────────────
     *
     * height: 1fr  =  "take all remaining vertical space".
     * After BigTitle (8 cells), timeline (~10), footer (1), and padding
     * are accounted for, 1fr stretches to fill everything else.
     * This makes metrics + verdict as tall as the terminal allows.
     */
    #hero-row {{
        width: 100%;
        height: 1fr;
        margin-bottom: 1;
    }}

    /* LEFT hero panel: metrics + challenge metadata */
    #metrics-box {{
        width: 38%;
        border: solid {DIM_BRAND};
        padding: 0 1;
        height: 100%;
        overflow-y: auto;    /* scroll if content is taller than the box */
    }}

    /* RIGHT hero panel: markdown verdict */
    #verdict-box {{
        width: 62%;
        border: solid {DIM_BRAND};
        padding: 0 1;
        height: 100%;
        margin-left: 1;
    }}

    /* Smaller and cyan-themed scrollbars for all containers */
    #metrics-box, VerdictMarkdown, #timeline-box{{
        scrollbar-size-vertical: 1;          
        scrollbar-color: #00e5cc;              
        scrollbar-background: #0d1a0d;         
        scrollbar-color-hover: #00ffff;        
        scrollbar-color-active: #00ff88;       
    }}

    /* ── Markdown styling ────────────────────────────────────────────────────
     *
     * Textual's Markdown widget creates named child widgets we can target:
     *   MarkdownH2         → ## headings
     *   MarkdownH3         → ### headings
     *   MarkdownFence      → ```code blocks```
     *   MarkdownInlineCode → `inline code`
     *
     * We override their colours to match our palette.
     */
    VerdictMarkdown {{
        background: transparent;
        color: {TEXT};
        padding: 1 1;
        height: 100%;
        overflow-y: auto;
    }}

    VerdictMarkdown MarkdownH2 {{
        color: {BRAND};
        text-style: bold;
    }}

    VerdictMarkdown MarkdownH3 {{
        color: {ACCENT};
        text-style: bold;
    }}

    VerdictMarkdown MarkdownFence {{
        background: #0c1f1c;
        color: {ACCENT_OK};
        padding: 0 1;
    }}

    VerdictMarkdown MarkdownInlineCode {{
        color: {BRAND};
        text-style: bold;
    }}

    /* ── TIMELINE: slim strip at the bottom ─────────────────────────────────
     *
     * Fixed height of 10 cells — just enough to show a few log lines.
     * The player can scroll inside it if there are more rows.
     * Keeping it slim means it doesn't compete with the hero panels.
     */
    #timeline-box {{
        width: 100%;
        height: 10;
        border: solid {DIM_BRAND};
        padding: 0 2;
        padding-top: 1;
        overflow-y: auto;
    }}

    TimelineRow {{
        height: 1;
        width: 100%;
    }}

    EOFMarker {{
        height: 1;
        margin-top: 1;
    }}

    /* ── Footer: key hints docked to the very bottom edge ── */
    #footer-bar {{
        width: 100%;
        height: 1;
        background: {DIM_BRAND};
        color: {BRAND};
        dock: bottom;
        padding: 0 2;
        content-align: left middle;
    }}
    """

    # Key bindings: (key, action_method_name, description)
    BINDINGS = [
        ("q",     "quit",           "Quit"),
        ("enter", "return_browser", "Return to browser"),
        ("h",     "view_history",   "View History"),
    ]

    def compose(self) -> ComposeResult:
        """
        Lay out the screen like arranging furniture in a room.

        `yield widget`           → place this widget here
        `with Container(): ...`  → place the following widgets INSIDE this container
        """

        with Vertical(id="root-container"):

            # ── 1. ASCII art title ─────────────────────────────────────────────
            yield BigTitle()

            # ── 2. HERO ROW: metrics (left) + verdict (right) ─────────────────
            #
            # This Horizontal container stretches to fill most of the screen
            # (via "height: 1fr" in the CSS).  The two panels inside it are
            # the most important things on screen, so they get the most space.
            #
            # Visual:
            #   ┌─ #hero-row ────────────────────────────────────────┐
            #   │  ┌─ #metrics-box (38%) ──┐ ┌─ #verdict-box (62%) ─┐ │
            #   │  │  metadata + metrics   │ │  markdown verdict    │ │
            #   │  └───────────────────────┘ └──────────────────────┘ │
            #   └────────────────────────────────────────────────────┘

            with Horizontal(id="hero-row"):

                # LEFT: metrics panel (also contains challenge metadata)
                with Vertical(id="metrics-box"):
                    # yield SectionHeader("METRICS")
                    yield MetricsPanel()

                # RIGHT: scrollable markdown verdict
                with Vertical(id="verdict-box"):
                    # yield SectionHeader("SYSTEM_VERDICT")
                    # Pass the active markdown string in as the first argument.
                    # Textual renders it with full formatting automatically.
                    yield VerdictMarkdown(ACTIVE_VERDICT_MD, id="verdict-md")

            # ── 3. TIMELINE: slim scrollable strip ────────────────────────────
            #
            # Fixed at 10 cells tall. Visible but clearly secondary.
            # The player can scroll it without it dominating the screen.

            with ScrollableContainer(id="timeline-box"):
                # yield SectionHeader("TIMELINE")
                for timestamp, command, exit_code in TIMELINE_ROWS:
                    yield TimelineRow(timestamp, command, exit_code)
                yield EOFMarker()

            # ── 4. Footer ─────────────────────────────────────────────────────
            # dock: bottom in CSS pins this to the screen edge regardless of content.
            yield Static(
                "[Enter] RETURN TO BROWSER    [H] VIEW HISTORY    [Q] QUIT",
                id="footer-bar"
            )

    def on_mount(self) -> None:
        """Runs once after compose(). We set the terminal tab title."""
        result_word = "PASS" if IS_PASSING else "FAIL"
        self.title = f"{result_word} — {CHALLENGE['id']} {CHALLENGE['title']}"
        self.query_one("#metrics-box").border_title = "║ METRICS ║"
        self.query_one("#verdict-box").border_title = "║ SYSTEM_VERDICT ║"
        self.query_one("#timeline-box").border_title = "║ TIMELINE ║"


    def action_return_browser(self) -> None:
        self.notify("Returning to browser...", title="Navigation", timeout=2)

    def action_view_history(self) -> None:
        self.notify("Opening history...", title="History", timeout=2)

    def action_quit(self) -> None:
        self.exit()


# ══════════════════════════════════════════════════════════════════════════════
#  ▶  ENTRY POINT
# ══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = VerdictScreen()
    app.run()