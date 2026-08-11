# ui/screens/history.py
"""
CLICE - SESSION HISTORY
========================
"""

from datetime import datetime
from pathlib import Path
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import Static, DataTable, Input
from textual.screen import Screen
from textual.binding import Binding
from ui.screens.data.history import SESSION_DATA
from ui.widgets.footer import Footer
from ui.widgets.history.modal import ConfirmModal
from ui.widgets.history.search import SearchBar
from ui.widgets.history.status import StatsBar
from ui.services.history import HistoryService
from ui.screens.verdict import VerdictScreen

ALLOW_DUMMY_DATA=False

class HistoryScreen(Screen):
    """Session history screen — browse, search, and manage past sessions."""

    ansi_color = False

    BINDINGS = [
        Binding("d", "delete_row", "Delete", show=False),
        Binding("c", "clear_all", "Clear All", show=False),
        Binding("space", "view_session", "View", show=False),
        Binding("escape", "app.pop_screen", "Back", show=True),
    ]

    CSS_PATH = Path(__file__).parent / "history.tcss"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.history = HistoryService()
        self._sessions = []  # Will hold session data from history

    def compose(self) -> ComposeResult:
        self.stats_bar = StatsBar(id="stats_bar")
        yield self.stats_bar
        yield SearchBar(id="search_bar")
        yield Vertical(
            DataTable(id="session_table"),
            Static(
                "( no sessions found )\nComplete a challenge to see results here.",
                id="empty_state",
            ),
            id="table_panel",
        )
        yield Footer()

    def on_mount(self) -> None:
        """Set up the table and load sessions."""
        self.query_one(Footer).set_screen("history")
        self._load_sessions()

        table = self.query_one("#session_table", DataTable)
        table.cursor_type = "row"
        table.zebra_stripes = False
        table.cell_padding = 3
        table.header_height = 3

        table.add_column("\n#\n", width=8)
        table.add_column("\nTIMESTAMP\n", width=24)
        table.add_column("\nCHALLENGE\n", width=28)
        table.add_column("\nDURATION\n", width=16)
        table.add_column("\nCMDS\n", width=12)
        table.add_column("\nSTATUS\n", width=18)

        self.refresh_table()

    def on_screen_resume(self) -> None:
        """Fires every time this cached screen becomes active again (e.g.
        popped back to after finishing a challenge), unlike on_mount which
        only fires once. Re-reads from disk so a just-completed session
        actually shows up without needing a fresh screen instance."""
        self._load_sessions()
        self.refresh_table()
        self.update_stats()

    def _load_sessions(self) -> None:
        """Load sessions from HistoryService."""
        self._sessions = self.history.get_sessions() 
        if not self._sessions and ALLOW_DUMMY_DATA:
            # Convert dummy data to session dicts
            self._sessions = self._convert_dummy_data(SESSION_DATA)
        self.stats_bar.update_stats(self._sessions)

    def _convert_dummy_data(self, dummy_data: list) -> list:
        """Convert dummy data format to session dict format."""
        sessions = []
        for row in dummy_data:
            # row: (number, timestamp, challenge, duration, cmds, status)
            sessions.append({
                "session_id": row[0],
                "challenge_code": row[2],
                "challenge_title": row[2],
                "started_at": row[1],
                "submitted_at": row[1],  # dummy has no end time
                "duration_seconds": self._parse_duration(row[3]),
                "command_count": int(row[4]),
                "status": row[5],
                "goal_reached": row[5] == "PASS",
            })
        return sessions

    def _parse_duration(self, duration_str: str) -> float:
        """Parse HH:MM:SS duration to seconds."""
        try:
            parts = duration_str.split(":")
            if len(parts) == 3:
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            elif len(parts) == 2:
                return int(parts[0]) * 60 + int(parts[1])
            else:
                return float(duration_str)
        except:
            return 0.0

    def refresh_table(self) -> None:
        """Refresh the table with current data and search filter."""
        table = self.query_one("#session_table", DataTable)
        table.clear()

        search_box = self.query_one("#search_box", Input)
        search_text = search_box.value

        # Parse the search query
        search_widget = self.query_one("#search_bar", SearchBar)
        parsed = search_widget.parse_query(search_text)

        # Filter sessions
        filtered = []
        for session in self._sessions:
            if search_widget.matches_session(session, parsed):
                filtered.append(session)

        # Display filtered sessions
        for idx, session in enumerate(filtered, 1):
            status = session.get("status", "UNKNOWN")
            if status == "PASS":
                status_text = "[#4ade80][PASS] ✓[/#4ade80]"
            else:
                status_text = "[#f0656b][FAIL] ✗[/#f0656b]"

            # Format timestamp
            started = session.get("started_at", "")
            if started and len(started) >= 16:
                timestamp = started[:16]
            else:
                timestamp = "--:--"

            # Format duration
            duration_secs = session.get("duration_seconds", 0)
            hours = int(duration_secs // 3600)
            minutes = int((duration_secs % 3600) // 60)
            seconds = int(duration_secs % 60)
            duration = f"{hours:02d}:{minutes:02d}:{seconds:02d}"

            table.add_row(
                f"\n{idx}\n",
                f"\n{timestamp}\n",
                f"\n{session.get('challenge_code', 'Unknown')}\n",
                f"\n{duration}\n",
                f"\n{session.get('command_count', 0)}\n",
                f"\n{status_text}\n",
                height=3,
                key=session.get("session_id", str(idx)),
            )

        # Handle empty state
        empty_state = self.query_one("#empty_state", Static)
        if table.row_count == 0:
            if not self._sessions:
                empty_state.update("( no sessions yet )\nComplete a challenge to see results here.")
            else:
                empty_state.update(f"( no sessions match \"{search_box.value}\" )\nTry a different search term.")
            empty_state.add_class("visible")
            table.display = False
        else:
            empty_state.remove_class("visible")
            table.display = True

    def update_stats(self) -> None:
        """Update the stats bar with current data."""
        self.stats_bar.update_stats(self._sessions)

    # ── Event Handlers ─────────────────────────────────────────────────────

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "search_box":
            self.refresh_table()

    # ── Actions ────────────────────────────────────────────────────────────

    def action_delete_row(self) -> None:
        """Delete the selected session."""
        table = self.query_one("#session_table", DataTable)

        if table.row_count == 0:
            return

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        session_id = row_key.value

        # Find the session to get its challenge name
        session = next(
            (s for s in self._sessions if s.get("session_id") == session_id),
            None
        )
        if not session:
            return

        challenge_name = session.get("challenge_code", session_id)

        def handle_answer(confirmed: bool | None) -> None:
            if confirmed:
                self.history.delete_session(session_id)
                self._sessions = self.history.get_sessions()
                self.refresh_table()
                self.update_stats()

        self.app.push_screen(
            ConfirmModal(f"Delete session {challenge_name}? This can't be undone."),
            handle_answer,
        )

    def action_clear_all(self) -> None:
        """Clear all sessions."""
        if not self._sessions:
            return

        def handle_answer(confirmed: bool | None) -> None:
            if confirmed:
                self.history.clear_all()
                self._sessions = self.history.get_sessions()
                self.refresh_table()
                self.update_stats()

        self.app.push_screen(
            ConfirmModal("Clear ALL sessions? This can't be undone."),
            handle_answer,
        )

    def action_view_session(self) -> None:
        """View the selected session's verdict."""
        table = self.query_one("#session_table", DataTable)

        if table.row_count == 0:
            return

        row_key, _ = table.coordinate_to_cell_key(table.cursor_coordinate)
        session_id = row_key.value

        # Load the full session log
        full_log = self.history.get_session(session_id)
        if not full_log:
            self.notify("Session not found", title="Error", severity="error")
            return

        # Reconstruct challenge dict
        challenge = {
            "id": full_log.get("challenge_id"),
            "code": full_log.get("challenge_code"),
            "title": full_log.get("challenge_title"),
            "category": full_log.get("category", "CLI"),
            "difficulty": full_log.get("difficulty", "intermediate"),
            "tags": full_log.get("tags", []),
            "objectives": full_log.get("objectives", []),
        }

        self.app.push_screen(VerdictScreen(challenge, full_log, session_id))