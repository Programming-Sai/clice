# ui/widgets/status_bar.py
from textual.containers import Horizontal
from textual.widgets import Static

class StatusBar(Static):
    """Shared status bar widget"""
    
    def compose(self):
        with Horizontal(id="status-left"):
            with Horizontal(id="status-left"):
                yield Static("[cyan b]\[N][/cyan b] [dim]NEW_SESSION[/dim]  ")
                yield Static("[cyan b]\[B][/cyan b] [dim]BROWSER[/dim]  ")
                yield Static("[cyan b]\[H][/cyan b] [dim]HISTORY[/dim]  ")
                yield Static("[cyan b]\[S][/cyan b] [dim]SETTINGS[/dim]  ")
                yield Static("[cyan b]\[Q][/cyan b] [dim]QUIT[/dim]")

            yield Static(
                "[dim]TTY: PTS/0   V1.0.4-STABLE   [/dim][cyan b]STATUS: READY ▐▐[/cyan b]",
                id="status-right"
            )