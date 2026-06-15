from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from ui.widgets.utils.design import (
    ACCENT_ERR, ACCENT_OK, BRAND, DIM_BRAND, TEXT, DIM_TEXT, get_difficulty_color
)

class MetricsPanel(Static):
    """Left panel: challenge metadata + run metrics."""

    total_commands: reactive[int] = reactive(0)
    time_elapsed: reactive[str] = reactive("00:00:00")
    correctness: reactive[float] = reactive(0.0)
    error_rate: reactive[float] = reactive(0.0)

    def __init__(self, challenge: dict, is_passing: bool, **kwargs):
        super().__init__(**kwargs)
        self.challenge = challenge
        self.is_passing = is_passing
        self._update_metrics_from_session()

    def _update_metrics_from_session(self):
        """Parse session log if available (override in on_mount)."""
        # For demo, set random values based on pass/fail
        import random
        if self.is_passing:
            self.total_commands = random.randint(3, 10)
            self.correctness = random.uniform(85, 100)
            self.error_rate = random.uniform(0, 10)
            total_seconds = random.randint(30, 180)
        else:
            self.total_commands = random.randint(10, 25)
            self.correctness = random.uniform(0, 60)
            self.error_rate = random.uniform(30, 70)
            total_seconds = random.randint(120, 600)

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        self.time_elapsed = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def render(self) -> Text:
        t = Text()
        c = self.challenge

        def row(label: str, value: str, value_style: str = None) -> None:
            t.append(f" {label:<20}", style=DIM_TEXT)
            vs = value_style or (ACCENT_OK if self.is_passing else ACCENT_ERR)
            t.append(f"{value}\n", style=vs)

        t.append("\n")
        row("TOTAL COMMANDS:", str(self.total_commands))
        row("TIME ELAPSED:", self.time_elapsed, BRAND)
        row("CORRECTNESS (%):", f"{self.correctness:.1f}%")
        row("ERROR RATE (%):", f"{self.error_rate:.1f}%")
        t.append(" " + "─" * 32 + "\n", style=DIM_BRAND)

        # Score (simplified: correctness as integer)
        score = int(self.correctness)
        # Progress bar
        bar_width = 18
        filled = int(bar_width * score / 100)
        empty = bar_width - filled
        t.append("\n SCORE\t ", style=DIM_TEXT)
        t.append("[", style=DIM_BRAND)
        t.append("█" * filled, style=ACCENT_OK if self.is_passing else ACCENT_ERR)
        t.append(" " * empty, style=DIM_BRAND)
        t.append("] ", style=DIM_BRAND)
        t.append(f"{score}%", style=ACCENT_OK if self.is_passing else ACCENT_ERR)

        t.append("\n\n")
        t.append(" " + "=" * 32 + "\n", style=DIM_BRAND)
        t.append("\n\n")

        t.append(f" {c['id']}  ", style=f"dim {BRAND}")
        t.append(c["title"] + "\n", style=f"bold {BRAND}")
        t.append(" " + "─" * 32 + "\n", style=DIM_BRAND)

        t.append(f" {'CATEGORY':<12}", style=DIM_TEXT)
        t.append(c["category"] + "\n", style=TEXT)
        t.append(f" {'DIFFICULTY':<12}", style=DIM_TEXT)
        diff_clean = c["difficulty"].split("[")[0].strip().lower()
        t.append(c["difficulty"] + "\n", style=get_difficulty_color(diff_clean))

        t.append(f" {'TAGS':<12}", style=DIM_TEXT)
        for tag in c.get("tags", []):
            t.append(f" {tag} ", style=f"bold black on {BRAND}")
            t.append(" ")
        t.append("\n")
        t.append(" " + "─" * 32 + "\n", style=DIM_BRAND)

        t.append(" OBJECTIVES\n", style=DIM_TEXT)
        for obj in c.get("objectives", []):
            t.append("  ▸ ", style=BRAND)
            t.append(obj + "\n", style=TEXT)
        



        
        return t