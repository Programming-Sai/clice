from textual.app import ComposeResult
from textual.widgets import Static, DataTable


SHOW_EMPTY_STATE = True


ACTIVITY_DATA = [
    ("2023.10.24 14:12", "GREP-BASICS",     "03:12", "PASS"),
    ("2023.10.24 13:55", "TAR-ARCHIVE",     "01:45", "FAIL"),
    ("2023.10.24 13:01", "CRON-JOBS-V1",    "00:52", "PASS"),
    ("2023.10.24 12:45", "SUDO-LINT",       "00:12", "PASS"),
    ("2023.10.24 12:20", "SSH-KEYGEN-WK",   "04:30", "PASS"),
    ("2023.10.24 11:58", "AWK-FILTER",      "02:05", "PASS"),
    ("2023.10.24 11:34", "CHMOD-DRILL",     "01:10", "FAIL"),
    ("2023.10.24 11:10", "FIND-EXEC",       "03:44", "PASS"),
    ("2023.10.24 10:52", "CURL-HEADERS",    "00:38", "PASS"),
    ("2023.10.24 10:30", "PIPE-CHAIN",      "02:21", "PASS"),
    ("2023.10.24 10:05", "ENV-VARS-V2",     "01:55", "FAIL"),
    ("2023.10.24 09:48", "NETSTAT-SCAN",    "00:47", "PASS"),
    ("2023.10.24 09:22", "RSYNC-BACKUP",    "05:13", "PASS"),
    ("2023.10.24 09:01", "DIFF-PATCH",      "01:29", "PASS"),
    ("2023.10.24 08:44", "KILL-SIGNAL",     "00:33", "FAIL"),
    ("2023.10.24 08:20", "TMUX-LAYOUT",     "02:58", "PASS"),
    ("2023.10.24 08:00", "GIT-REBASE",      "04:07", "PASS"),
    ("2023.10.23 23:55", "REGEX-CAPTURE",   "03:30", "PASS"),
    ("2023.10.23 23:30", "XARGS-BUILD",     "01:14", "FAIL"),
    ("2023.10.23 23:10", "LESS-SEARCH",     "00:28", "PASS"),
    ("2023.10.23 22:48", "SED-REPLACE",     "02:44", "PASS"),
    ("2023.10.23 22:20", "PS-MONITOR",      "01:03", "PASS"),
    ("2023.10.23 22:00", "DISK-USAGE",      "00:55", "PASS"),
    ("2023.10.23 21:38", "CRONTAB-EDIT",    "03:18", "FAIL"),
    ("2023.10.23 21:10", "SSH-TUNNEL",      "04:52", "PASS"),
]




class ActivityPanel(Static):
    def compose(self) -> ComposeResult:
        yield Static("║ RECENT ATTEMPTS ║", classes="panel-title")
        if SHOW_EMPTY_STATE:
            yield Static(
                "─── NO ATTEMPTS YET ───\n\n"
                "Press [N] to start your first challenge.",
                id="empty-state"
            )
        else:
            yield DataTable(show_cursor=True)

    def on_mount(self) -> None:
        if not SHOW_EMPTY_STATE:
            table = self.query_one(DataTable)
            table.add_column("TIMESTAMP",  width=22)
            table.add_column("CHALLENGE",  width=20)
            table.add_column("DURATION",   width=12)
            table.add_column("RESULT",     width=10)

            for timestamp, task_id, duration, status in ACTIVITY_DATA:
                styled_task   = f"[cyan]{task_id}[/cyan]"
                styled_status = "[cyan b][PASS][/cyan b]" if status == "PASS" else "[red b][FAIL][/red b]"
                table.add_row(timestamp, styled_task, duration, styled_status)

        self.border_title = "03 / HISTORY"

