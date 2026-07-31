# We need to "import" (borrow) some tools from the textual toy box.
from datetime import datetime

from textual.app import ComposeResult          # App = the whole program. ComposeResult = the list of widgets we build.
from textual.containers import Horizontal  # Boxes that line widgets up in a row, or stack them up.
from textual.widgets import Static                  # Binding = "when this key is pressed, run this action."



# ---------------------------------------------------------------------------
# STEP 3: THE STATS BAR  (TOTAL SESSIONS / SUCCESS RATE / AVG. TIME)
# ---------------------------------------------------------------------------
class StatsBar(Horizontal):
    """
    Shows the little summary numbers near the top, like a scoreboard.

    KID-FRIENDLY BUG STORY: the very first version of this put the label
    ("TOTAL SESSIONS") and the value ("12 SESSIONS") in two separate little
    Static widgets, stacked inside a "Vertical" box set to width: auto.
    That's what made them vanish on wide screens! When a box says
    "auto", Textual has to measure its children to know how wide to make
    it - and stacking two auto-width things inside another auto-width box
    sometimes confuses that measurement, so the box shrank to nothing.

    THE FIX: each stat below is now just ONE Static widget with the label
    and value written on two lines inside a single string (using "\\n" to
    make a new line), and we give it a fixed, explicit width. One widget,
    one clear size - nothing left for Textual to get confused about.
    """

    def __init__(self, sessions: list = None, **kwargs):
        super().__init__(**kwargs)
        self.sessions = sessions or []
        self._stat_total = None
        self._stat_pass_rate = None
        self._stat_avg_time = None

    def compose(self) -> ComposeResult:
        self._stat_total = Static(
            "[dim]TOTAL SESSIONS[/dim]\n[bold]0 SESSIONS[/bold]",
            id="stat_total",
            classes="stat_block",
        )
        self._stat_pass_rate = Static(
            "[dim]SUCCESS RATE[/dim]\n[bold #4ade80]0% PASS[/bold #4ade80]",
            classes="stat_block",
        )
        self._stat_avg_time = Static(
            "[dim]AVG. TIME[/dim]\n[bold #e0b038]00:00:00 AVG[/bold #e0b038]",
            classes="stat_block",
        )

        yield self._stat_total
        yield self._stat_pass_rate
        yield self._stat_avg_time

    def update_stats(self, sessions: list) -> None:
        """Update the stats bar with new session data."""
        self.sessions = sessions
        self._update_total()
        self._update_pass_rate()
        self._update_avg_time()

    def _update_total(self) -> None:
        """Update total sessions count."""
        total = len(self.sessions)
        label = "SESSION" if total == 1 else "SESSIONS"
        self._stat_total.update(f"[dim]TOTAL SESSIONS[/dim]\n[bold]{total} {label}[/bold]")

    def _update_pass_rate(self) -> None:
        """Update pass rate percentage."""
        if not self.sessions:
            self._stat_pass_rate.update("[dim]SUCCESS RATE[/dim]\n[bold #4ade80]0% PASS[/bold #4ade80]")
            return

        passed = sum(1 for s in self.sessions if s.get("goal_reached", False))
        rate = round((passed / len(self.sessions)) * 100)
        color = "#4ade80" if rate >= 50 else "#ff4444"  # Green if >= 50%, red if below
        self._stat_pass_rate.update(
            f"[dim]SUCCESS RATE[/dim]\n[bold {color}]{rate}% PASS[/bold {color}]"
        )

    def _update_avg_time(self) -> None:
        """Update average session time."""
        if not self.sessions:
            self._stat_avg_time.update("[dim]AVG. TIME[/dim]\n[bold #e0b038]00:00:00 AVG[/bold #e0b038]")
            return

        total_seconds = 0
        count = 0

        for session in self.sessions:
            # Try to get duration from session data
            duration = session.get("duration_seconds")
            if duration is None:
                # Calculate from started_at and submitted_at
                try:
                    started = session.get("started_at", "")
                    submitted = session.get("submitted_at", "")
                    if started and submitted:
                        start = datetime.fromisoformat(started)
                        end = datetime.fromisoformat(submitted)
                        duration = (end - start).total_seconds()
                    else:
                        continue
                except (ValueError, TypeError):
                    continue

            total_seconds += duration
            count += 1

        if count == 0:
            self._stat_avg_time.update("[dim]AVG. TIME[/dim]\n[bold #e0b038]00:00:00 AVG[/bold #e0b038]")
            return

        avg_seconds = total_seconds / count
        hours = int(avg_seconds // 3600)
        minutes = int((avg_seconds % 3600) // 60)
        seconds = int(avg_seconds % 60)

        time_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        self._stat_avg_time.update(
            f"[dim]AVG. TIME[/dim]\n[bold #e0b038]{time_str} AVG[/bold #e0b038]"
        )

