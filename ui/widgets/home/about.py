from textual.app import  ComposeResult
from textual.widgets import Static


class AboutPanel(Static):
    def compose(self) -> ComposeResult:
        yield Static("║ WHAT IS CLICE? ║", classes="panel-title")
        yield Static(
            "CLICE evaluates your command-line competence through\n"
            "timed, scored challenges. Each session presents a real\n"
            "task — you solve it in your terminal, CLICE grades it.\n\n"
            "No multiple choice. No theory. Just the shell.",
            id="about-text"
        )

    def on_mount(self) -> None:
        self.border_title = "01 / ABOUT"
