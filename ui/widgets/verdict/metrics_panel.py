from textual.widgets import Static
from textual.reactive import reactive
from rich.text import Text
from ui.widgets.utils.design import (
    ACCENT_ERR, ACCENT_OK, BRAND, DIM_BRAND, TEXT, DIM_TEXT, get_difficulty_color
)
from engine.evaluator import evaluate



class MetricsPanel(Static):
    """Left panel: challenge metadata + run metrics."""

    total_commands: reactive[int] = reactive(0)
    time_elapsed: reactive[str] = reactive("00:00:00")
    correctness: reactive[float] = reactive(0.0)
    error_rate: reactive[float] = reactive(0.0)

    def __init__(self, challenge: dict, session_log: dict, is_passing: bool, **kwargs):
        super().__init__(**kwargs)
        self.challenge = challenge
        self.session_log = session_log
        self.is_passing = is_passing
        self._update_metrics_from_session()

    def _update_metrics_from_session(self):
        """Compute metrics from session log using the evaluator."""
        try:
            # Use the evaluator to compute metrics
            metrics = evaluate(self.session_log)
            
            self.total_commands = metrics["command_count"]
            self.error_rate = metrics["error_rate"]
            self.correctness = metrics["correctness"] * 100  # Convert to percentage
            
            # Format time
            time_seconds = metrics["time_seconds"]
            hours = int(time_seconds // 3600)
            minutes = int((time_seconds % 3600) // 60)
            seconds = int(time_seconds % 60)
            self.time_elapsed = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        except Exception as e:
            # Fallback to defaults if evaluator fails
            self.total_commands = 0
            self.error_rate = 0.0
            self.correctness = 0.0
            self.time_elapsed = "00:00:00"

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

        t.append("\n")
        t.append(" " + "=" * 32 + "\n", style=DIM_BRAND)
        t.append("\n")

        t.append(f" {c['code']}  ", style=f"dim {BRAND}")
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