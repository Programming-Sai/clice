"""
CLICE_CONSOLE_V2.0.4 // CHALLENGE_BROWSER
==========================================
"""

from pathlib import Path
from textual.screen import Screen
from textual.app import ComposeResult
from textual.widgets import Static, ListView, Input, Markdown
from textual.containers import Horizontal, Vertical
from textual import on
from textual.binding import Binding
from ui.screens.data.challenges import CHALLENGES
from ui.screens.session import SessionScreen
from ui.widgets.challenges.challenge_list_item import ChallengeListItem
from ui.widgets.challenges.detail_panel import DetailPanel
import re

from ui.widgets.challenges.search_input import SearchInput


class BrowserScreen(Screen):
    CSS_PATH = Path(__file__).parent / "browser.tcss"

    BINDINGS = [
        Binding("up",     "cursor_up",   "Navigate up",   show=True),
        Binding("down",   "cursor_down", "Navigate down", show=True),
        Binding("slash",  "search",      "Search",        show=True),
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("ctrl+enter", "start_challenge", "Start", show=True),
    ]

    _active_item: ChallengeListItem | None = None

    def compose(self) -> ComposeResult:
        with Horizontal(id="main-area"):
            with Vertical(id="left-panel"):
                yield Static("CHALLENGE_INDEX", id="left-panel-label")
                with ListView(id="challenge-list"):
                    for ch in CHALLENGES:
                        yield ChallengeListItem(ch)

            with Vertical(id="right-panel"):
                yield Static("CHALLENGE_DETAILS", id="right-panel-label")
                yield DetailPanel(id="detail-panel")

        with Horizontal(id="search-bar"):
            yield Static("> SEARCH_QUERY:", id="search-prefix")
            yield SearchInput(
                placeholder="search... | title:x | cat:file | diff:beginner | /regex/ | title:/regex/",
                id="search-input",
            )

        with Horizontal(id="bottom-bar"):
            yield Static(
                "[UP/DOWN] NAVIGATE   [ENTER] SELECT   [/] SEARCH   [ESC] BACK",
                id="bottom-keys",
            )
            yield Static(
                "CONN: OK   MEM: 128MB   MODE: READ_ONLY",
                id="bottom-sysinfo",
            )

    def on_mount(self) -> None:
        lv = self.query_one("#challenge-list", ListView)
        if CHALLENGES:
            first = lv.query(".challenge-item").first(ChallengeListItem)
            self._set_active(first)
            self.query_one("#detail-panel", DetailPanel).update_challenge(CHALLENGES[0])
        # Focus search on mount as requested
        self.query_one("#search-input", Input).focus()

    def _set_active(self, item: ChallengeListItem | None) -> None:
        if self._active_item is not None:
            self._active_item.remove_class("active")
        self._active_item = item
        if item is not None:
            item.add_class("active")

    @on(ListView.Highlighted)
    def on_list_highlighted(self, event: ListView.Highlighted) -> None:
        item = event.item
        if isinstance(item, ChallengeListItem):
            self._set_active(item)
            self.query_one("#detail-panel", DetailPanel).update_challenge(item.challenge)

    @on(ListView.Selected)
    def on_list_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if isinstance(item, ChallengeListItem):
            self._set_active(item)
            self.query_one("#detail-panel", DetailPanel).update_challenge(item.challenge)

    def action_cursor_up(self) -> None:
        self.query_one("#challenge-list", ListView).action_cursor_up()

    def action_cursor_down(self) -> None:
        self.query_one("#challenge-list", ListView).action_cursor_down()

    def action_search(self) -> None:
        self.query_one("#search-input", Input).focus()

    @on(Input.Changed, "#search-input")
    def on_search_changed(self, event: Input.Changed) -> None:
        query = event.value.strip()

        field_map = {
            "title": "title",
            "cat":   "category",
            "id":    "id",
            "diff":  "difficulty",
            "desc":  "description",
        }

        def match_challenge(ch: dict, tokens: list) -> bool:
            for token in tokens:
                if ":" in token:
                    field, _, value = token.partition(":")
                    key = field_map.get(field.strip().lower())
                    if not key:
                        continue
                    value = value.strip()
                    # scoped regex: title:/pattern/
                    if value.startswith("/") and value.endswith("/") and len(value) > 2:
                        try:
                            pattern = re.compile(value[1:-1], re.IGNORECASE)
                            if not pattern.search(ch.get(key, "")):
                                return False
                        except re.error:
                            return False
                    else:
                        if value.lower() not in ch.get(key, "").lower():
                            return False
                else:
                    # bare word — must appear somewhere in the challenge
                    t = token.lower()
                    haystack = " ".join([
                        ch["id"].lower(), ch["title"].lower(),
                        ch["category"].lower(), ch["description"].lower(),
                        ch.get("markdown", "").lower(),
                    ])
                    if t not in haystack:
                        return False
            return True

        if not query:
            matching = CHALLENGES

        elif query.startswith("/") and query.endswith("/") and len(query) > 2:
            # global regex mode
            try:
                pattern = re.compile(query[1:-1], re.IGNORECASE)
                matching = [
                    ch for ch in CHALLENGES
                    if pattern.search(" ".join([
                        ch["id"], ch["title"], ch["category"],
                        ch["description"], ch.get("markdown", "")
                    ]))
                ]
            except re.error:
                matching = []

        else:
            # tokenize on whitespace — each token is ANDed
            tokens = query.split()
            matching = [ch for ch in CHALLENGES if match_challenge(ch, tokens)]

        lv = self.query_one("#challenge-list", ListView)
        lv.clear()
        self._active_item = None

        for ch in matching:
            lv.append(ChallengeListItem(ch))

        detail = self.query_one("#detail-panel", DetailPanel)
        if matching:
            first = lv.query(".challenge-item").first(ChallengeListItem)
            self._set_active(first)
            detail._restore_all()              # ← restore hidden widgets first
            detail.update_challenge(matching[0])
            self._show_results_state()
        else:
            self._show_empty_state(event.value)


    @on(Input.Submitted, "#search-input")
    def on_search_submitted(self, _: Input.Submitted) -> None:
        self.query_one("#challenge-list", ListView).focus()
    
    def action_start_challenge(self) -> None:
        """Start the currently selected challenge."""
        if not self._active_item:
            self.app.notify("No challenge selected", title="CLICE")
            return
        
        challenge = self._active_item.challenge
        
        # Load the challenge container
        
        try:
            # Push session screen with challenge and container
            self.app.push_screen(SessionScreen(challenge, True, True))
        except Exception as e:
            self.app.notify(f"Failed to start challenge: {e}", title="Error", severity="error")

    def on_key(self, event) -> None:
        if event.key == "up":
            event.prevent_default()
            event.stop()
            self.action_cursor_up()
            return

        if event.key == "down":
            event.prevent_default()
            event.stop()
            self.action_cursor_down()
            return

        if event.key == "alt+x":
            event.prevent_default()
            event.stop()
            self.action_start_challenge()
            return

    def _show_empty_state(self, query: str) -> None:
        """Hide list, show centered no-results message."""
        self.query_one("#left-panel").display = False
        detail = self.query_one("#detail-panel", DetailPanel)
        detail.show_empty_state(query)

    def _show_results_state(self) -> None:
        """Restore list panel."""
        self.query_one("#left-panel").display = True


