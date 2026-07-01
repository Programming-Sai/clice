
from textual.widgets import (ListItem, Label)
from textual.app import ComposeResult
from textual.containers import Vertical


# ─────────────────────────────────────────────────────────────────────────────
# WIDGET: ChallengeListItem
# ─────────────────────────────────────────────────────────────────────────────

class ChallengeListItem(ListItem):
    """One row in the challenge list."""

    def __init__(self, challenge: dict) -> None:
        super().__init__()
        self.challenge = challenge
        self.add_class("challenge-item")

    def compose(self) -> ComposeResult:
        ch = self.challenge
        tags_str = "//".join(ch["tags"])
        with Vertical():
            yield Label(f"{ch['id'][:5]}: {ch['title']}", classes="item-title")
            yield Label(f"# {tags_str}", classes="item-tags")

