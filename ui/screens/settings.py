# ui/screens/settings.py
"""
SettingsScreen — live-wired settings editor
=============================================
Flat command grammar, typed against Config._SCHEMA:

    set <key> <value>      e.g.  set resources.memory 1g
    get <key>                reveal a value in full (unmasks the API key)
    reset <key>              revert one field to its .env default
    reset all                revert everything (asks for confirmation)
    undo                     step back through the last change (repeatable)
    help                     list every command and key you can use

Typing shows an inline ghost-text suggestion for the rest of the command;
Tab fills it in, Enter actually runs it - completing never submits by
itself.

All reads/writes go straight through the live Config instance, so nothing
here is hardcoded sample data - the table always reflects what the rest of
the app is actually using.
"""

import json

from textual.app import ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Static, DataTable, Input
from textual.screen import Screen
from textual.binding import Binding
from textual.suggester import Suggester

from ui.widgets.footer import Footer
from ui.widgets.history.modal import ConfirmModal
from ui.services.config import Config
from ui.services.settings_schema import (
    FIELDS,
    KEY_TO_ATTR as _KEY_TO_ATTR,
    ATTR_TO_KEY as _ATTR_TO_KEY,
    BOOL_TRUE as _BOOL_TRUE,
    BOOL_FALSE as _BOOL_FALSE,
    UNSET as _UNSET,
    cast_and_validate,
    display_value as _shared_display_value,
)
from ui.widgets.utils.design import PERSISTENT_NOTIFICATION_TIMEOUT


BRAND      = "#00e5cc"   # main teal  - borders, section headers, prompts
ACCENT_OK  = "#4ade80"   # bright green - success / "everything is fine"
ACCENT_ERR = "#ff4444"   # bright red   - errors
DIM_BORDER = "#1e3a3a"   # dark teal    - the color of most panel borders
BG         = "#0a0a0a"   # near-black background, used across every screen
DIM_TEXT   = "#888888"   # soft grey    - secondary/label text, hints


# ---------------------------------------------------------------------
# Column widths - a design DECISION, not a measurement
# ---------------------------------------------------------------------

KEY_WIDTH = 22
CURRENT_WIDTH = 22
DEFAULT_WIDTH = 22
DESCRIPTION_WIDTH = 30

CELL_PADDING = 1
COLUMN_WIDTHS = [KEY_WIDTH, CURRENT_WIDTH, DEFAULT_WIDTH, DESCRIPTION_WIDTH]
TABLE_WIDTH = (
    sum(COLUMN_WIDTHS)
    + (2 * CELL_PADDING * len(COLUMN_WIDTHS))
    + 4
)


# ---------------------------------------------------------------------
# FIELDS - the single source of truth for what this screen shows.
# (display key, Config attribute, human description)
# The display key is what the user types in `set`/`get`/`reset`;
# the Config attribute is what actually gets read/written.
# ---------------------------------------------------------------------
# FIELDS, _KEY_TO_ATTR, _ATTR_TO_KEY, _BOOL_TRUE, _BOOL_FALSE, _UNSET now
# live in ui/services/settings_schema.py, shared with the CLI's
# `clice set`/`get`/`reset` commands so both stay in sync automatically.

_VERBS = ("set", "get", "reset", "undo", "help")

_HELP_TEXT = (
    "Commands:\n"
    "  set <key> <value>   change a setting, e.g. set resources.memory 1g\n"
    "  get <key>           reveal a value in full (unmasks the API key)\n"
    "  reset <key>         revert one setting to its default\n"
    "  reset all           revert every setting (asks to confirm)\n"
    "  undo                step back through your last change\n\n"
    "Keys:\n"
    + "\n".join(f"  {key}" for key, _, _ in FIELDS)
)


class CommandSuggester(Suggester):
    """Ghost-text completion for the settings command line.

    Suggests the rest of the verb, then the rest of the key, then (for
    boolean fields only) the rest of the value - always as a full-value
    completion, since that's what Input's suggester protocol expects.
    """

    def __init__(self) -> None:
        super().__init__(use_cache=False, case_sensitive=False)

    async def get_suggestion(self, value: str) -> str | None:
        if not value:
            return None
        parts = value.split(" ")

        # Completing the verb itself (no space typed yet).
        if len(parts) == 1:
            partial = parts[0].lower()
            for word in _VERBS:
                if word.startswith(partial) and word != partial:
                    return word
            return None

        verb = parts[0].lower()

        # Completing the key (second token).
        if len(parts) == 2 and verb in ("set", "get", "reset"):
            pool = [key for key, _, _ in FIELDS] + (["all"] if verb == "reset" else [])
            partial = parts[1].lower()
            for key in pool:
                if key.startswith(partial) and key != partial:
                    return f"{verb} {key}"
            return None

        # Completing a boolean value (third token) for `set`.
        if len(parts) == 3 and verb == "set":
            key = parts[1].lower()
            attr = _KEY_TO_ATTR.get(key)
            if attr and Config._SCHEMA[attr][1] is bool:
                partial = parts[2].lower()
                for word in ("on", "off"):
                    if word.startswith(partial) and word != partial:
                        return f"{verb} {key} {word}"
            return None

        return None


APP_CSS = f"""
#content-wrap {{
    width: auto;
    height: auto;
}}

#table-box {{
    border: tall {DIM_BORDER};
    margin: 1 0;
    padding: 0 1;
    width: {TABLE_WIDTH};
    height: auto;
}}

#config-table {{
    background: {BG};
    color: {DIM_TEXT};
    width: 100%;
    height: auto;
}}

DataTable > .datatable--header {{
    color: {DIM_TEXT};
    text-style: bold;
    background: {BG};
}}

DataTable > .datatable--cursor {{
    background: {BRAND};
    color: {BG};
}}

#command-box {{
    border: tall {DIM_BORDER};
    background: {BG};
    margin: 0 0 0 0;
    height: 3;
    align: left middle;
    width: {TABLE_WIDTH};
}}

#prompt-symbol {{
    color: {BRAND};
    text-style: bold;
    width: auto;
    padding: 0 0 0 1;
}}

#command-input {{
    background: {BG};
    border: none;
    color: {BRAND};
}}
#command-input:focus {{
    border: none;
}}

#status-line {{
    width: {TABLE_WIDTH};
    height: auto;
    margin: 0 0 1 0;
    padding: 0 1;
    color: {DIM_TEXT};
}}

#status-line.-error {{
    color: {ACCENT_ERR};
}}

#status-line.-ok {{
    color: {ACCENT_OK};
}}

#body {{
    height: 1fr;
    align: center top;
}}
"""


class SettingsScreen(Screen):
    """Live settings editor, backed directly by Config."""

    CSS = APP_CSS

    BINDINGS = [
        Binding("escape", "app.pop_screen", "Back", show=True),
        Binding("tab", "accept_suggestion", "Complete", show=False, priority=True),
        Binding("up", "history_prev", "Prev cmd", show=False, priority=True),
        Binding("down", "history_next", "Next cmd", show=False, priority=True),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.config = Config()
        # Stack of (label, snapshot) - snapshot maps attr -> its prior
        # override value (or _UNSET if it had none) at the moment right
        # before that change was applied. Popping and re-applying the
        # snapshot is the whole undo mechanism.
        self._undo_stack: list[tuple[str, dict]] = []
        # Shell-style command recall: the commands actually submitted, most
        # recent last. _history_index is None while not browsing; while
        # browsing, _history_draft holds whatever was being typed before
        # the first Up press, so Down can return to it past the newest entry.
        self._command_history: list[str] = []
        self._history_index: int | None = None
        self._history_draft: str = ""

    def check_action(self, action: str, parameters: tuple) -> bool | None:
        # History recall should only hijack Up/Down while the command input
        # itself is focused - otherwise it would swallow the arrow keys the
        # DataTable needs for its own cursor navigation.
        if action in ("history_prev", "history_next"):
            command_input = self.query_one("#command-input", Input)
            if self.focused is not command_input:
                return False
        return True

    # ── Compose / mount ───────────────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Vertical(id="body"):
            with Vertical(id="content-wrap"):
                with Vertical(id="table-box"):
                    yield DataTable(id="config-table", cursor_type="cell")

                with Horizontal(id="command-box"):
                    yield Static(">", id="prompt-symbol")
                    yield Input(
                        placeholder="set resources.memory 1g  (try `help`)",
                        id="command-input",
                        suggester=CommandSuggester(),
                    )

                yield Static("", id="status-line")

        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Footer).set_screen("settings")
        table = self.query_one("#config-table", DataTable)

        table.add_column("KEY", width=KEY_WIDTH)
        table.add_column("CURRENT", width=CURRENT_WIDTH)
        table.add_column("DEFAULT", width=DEFAULT_WIDTH)
        table.add_column("DESCRIPTION", width=DESCRIPTION_WIDTH)
        table.show_row_labels = False

        self._populate_table()

        table.cursor_coordinate = (0, 1)
        self.query_one("#command-input", Input).focus()

    # ── Table population ────────────────────────────────────────────────

    def _display_value(self, attr: str, value) -> str:
        return _shared_display_value(attr, value)

    def _populate_table(self) -> None:
        """(Re)build every row from the live Config instance."""
        table = self.query_one("#config-table", DataTable)
        table.clear()
        for key, attr, description in FIELDS:
            current = self._display_value(attr, getattr(self.config, attr))
            default = self._display_value(attr, self.config._env_defaults.get(attr))
            table.add_row(key, current, default, description, key=key)

    def _refresh_row(self, key: str) -> None:
        """Update just one row in place, keeping cursor position sane."""
        table = self.query_one("#config-table", DataTable)
        attr = _KEY_TO_ATTR[key]
        current = self._display_value(attr, getattr(self.config, attr))
        default = self._display_value(attr, self.config._env_defaults.get(attr))
        # DataTable.update_cell wants column keys, not labels - columns were
        # added in KEY/CURRENT/DEFAULT/DESCRIPTION order, so index 1 is
        # CURRENT and index 2 is DEFAULT.
        table.update_cell(key, table.ordered_columns[1].key, current)
        table.update_cell(key, table.ordered_columns[2].key, default)

    # ── Status line ──────────────────────────────────────────────────────

    def _set_status(self, message: str, kind: str = "info") -> None:
        status = self.query_one("#status-line", Static)
        status.remove_class("-error", "-ok")
        if kind == "error":
            status.add_class("-error")
        elif kind == "ok":
            status.add_class("-ok")
        status.update(message)

    # ── Command input ────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id != "command-input":
            return
        raw = event.value.strip()
        event.input.value = ""
        self._history_index = None
        if raw:
            # Skip recording an exact back-to-back repeat, same as a shell.
            if not self._command_history or self._command_history[-1] != raw:
                self._command_history.append(raw)
            self._handle_command(raw)

    def _handle_command(self, raw: str) -> None:
        parts = raw.split(maxsplit=2)
        cmd = parts[0].lower()

        if cmd == "set" and len(parts) == 3:
            self._cmd_set(parts[1], parts[2])
        elif cmd == "get" and len(parts) == 2:
            self._cmd_get(parts[1])
        elif cmd == "reset" and len(parts) == 2:
            self._cmd_reset(parts[1])
        elif cmd == "undo" and len(parts) == 1:
            self._cmd_undo()
        elif cmd == "help" and len(parts) == 1:
            self._cmd_help()
        else:
            self._set_status(
                f"Unrecognized command: '{raw}'. Type `help` to see everything you can type.",
                kind="error",
            )

    # ── Undo snapshotting ────────────────────────────────────────────────

    def _read_overrides(self) -> dict:
        path = self.config.settings_path
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}

    def _snapshot(self, attrs) -> dict:
        """Capture the current override state (or _UNSET) for each attr,
        right before it's about to change."""
        overrides = self._read_overrides()
        return {attr: overrides.get(attr, _UNSET) for attr in attrs}

    def _push_undo(self, label: str, snapshot: dict) -> None:
        self._undo_stack.append((label, snapshot))

    # ── set ──────────────────────────────────────────────────────────────

    def _cmd_set(self, key: str, raw_value: str) -> None:
        key = key.lower()
        attr = _KEY_TO_ATTR.get(key)
        if attr is None:
            self._set_status(f"Unknown setting '{key}'. Type `help` for the full list.", kind="error")
            return

        try:
            value = self._cast_and_validate(attr, raw_value)
        except ValueError as e:
            self._set_status(f"Invalid value for '{key}': {e}", kind="error")
            return

        self._push_undo(f"set {key}", self._snapshot([attr]))
        self.config.save(**{attr: value})
        self._refresh_row(key)
        self._set_status(f"Saved {key} = {self._display_value(attr, value)}", kind="ok")

    def _cast_and_validate(self, attr: str, raw_value: str):
        return cast_and_validate(attr, raw_value)

    # ── reset ────────────────────────────────────────────────────────────

    def _cmd_reset(self, key: str) -> None:
        key = key.lower()

        if key == "all":
            def handle_answer(confirmed: bool | None) -> None:
                if confirmed:
                    all_attrs = [attr for _, attr, _ in FIELDS]
                    self._push_undo("reset all", self._snapshot(all_attrs))
                    self.config.reset()
                    self._populate_table()
                    self._set_status("All settings reset to defaults", kind="ok")

            self.app.push_screen(
                ConfirmModal("Reset ALL settings to their defaults? This can't be undone (but `undo` will still work)."),
                handle_answer,
            )
            return

        attr = _KEY_TO_ATTR.get(key)
        if attr is None:
            self._set_status(f"Unknown setting '{key}'.", kind="error")
            return

        self._push_undo(f"reset {key}", self._snapshot([attr]))
        self.config.reset(attr)
        self._refresh_row(key)
        self._set_status(f"Reset {key} to default", kind="ok")

    # ── undo ─────────────────────────────────────────────────────────────

    def _cmd_undo(self) -> None:
        if not self._undo_stack:
            self._set_status("Nothing to undo", kind="error")
            return

        label, snapshot = self._undo_stack.pop()
        for attr, prior in snapshot.items():
            if prior is _UNSET:
                self.config.reset(attr)
            else:
                self.config.save(**{attr: prior})

        if len(snapshot) == len(FIELDS):
            self._populate_table()
        else:
            for attr in snapshot:
                self._refresh_row(_ATTR_TO_KEY[attr])

        self._set_status(f"Undid: {label}", kind="ok")

    # ── get (reveal a value in full) ────────────────────────────────────

    def _cmd_get(self, key: str) -> None:
        key = key.lower()
        attr = _KEY_TO_ATTR.get(key)
        if attr is None:
            self._set_status(f"Unknown setting '{key}'.", kind="error")
            return

        value = getattr(self.config, attr)
        display = value if value not in (None, "") else "(not set)"
        self.notify(f"{key} = {display}", title="CLICE", timeout=PERSISTENT_NOTIFICATION_TIMEOUT)
        self._set_status(f"Revealed {key} above (dismiss the notification to hide it again)")

    # ── help ─────────────────────────────────────────────────────────────

    def _cmd_help(self) -> None:
        self.notify(_HELP_TEXT, title="Settings help", timeout=12)
        self._set_status("Help shown above")

    # ── ghost-text autocomplete ─────────────────────────────────────────

    def action_accept_suggestion(self) -> None:
        command_input = self.query_one("#command-input", Input)
        if self.focused is command_input and command_input._suggestion:
            command_input.action_cursor_right()
        else:
            self.focus_next()

    # ── command history recall (Up/Down, like a shell) ─────────────────

    def action_history_prev(self) -> None:
        command_input = self.query_one("#command-input", Input)
        if not self._command_history:
            return
        if self._history_index is None:
            self._history_draft = command_input.value
            self._history_index = len(self._command_history) - 1
        elif self._history_index > 0:
            self._history_index -= 1
        command_input.value = self._command_history[self._history_index]
        command_input.action_end()

    def action_history_next(self) -> None:
        command_input = self.query_one("#command-input", Input)
        if self._history_index is None:
            return
        if self._history_index < len(self._command_history) - 1:
            self._history_index += 1
            command_input.value = self._command_history[self._history_index]
        else:
            self._history_index = None
            command_input.value = self._history_draft
        command_input.action_end()