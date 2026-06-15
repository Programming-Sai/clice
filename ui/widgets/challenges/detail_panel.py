from textual.app import ComposeResult
from textual.widgets import Static, Markdown
from textual.containers import Horizontal, Vertical, ScrollableContainer



# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────

def difficulty_class(difficulty: str) -> str:
    d = difficulty.upper()
    if d.startswith("BEGINNER"):
        return "diff-beginner"
    if d.startswith("INTERMEDIATE"):
        return "diff-intermediate"
    if d.startswith("ADVANCED"):
        return "diff-advanced"
    return "diff-beginner"



# ─────────────────────────────────────────────────────────────────────────────
# WIDGET: DetailPanel
# ─────────────────────────────────────────────────────────────────────────────

class DetailPanel(ScrollableContainer):
    """Right-hand detail panel."""

    def compose(self) -> ComposeResult:
        yield Static(r"\[ACTIVE_SESSION: NULL]", id="session-status")
        yield Static("# SELECT A CHALLENGE", id="detail-title")

        with Horizontal(id="detail-meta"):
            with Vertical():
                yield Static("DIFFICULTY:", id="meta-difficulty-label")
                yield Static("—", id="meta-difficulty-value")
            with Vertical():
                yield Static("CATEGORY:", id="meta-category-label")
                yield Static("—", id="meta-category-value")

        with Vertical(id="objectives-box"):
            yield Static("> OBJECTIVES", classes="section-heading")
            yield Static("[ ]  —", classes="objective-item", id="obj-0")
            yield Static("[ ]  —", classes="objective-item", id="obj-1")
            yield Static("[ ]  —", classes="objective-item", id="obj-2")

        yield Static("> DESC_CONTENT", classes="section-heading")
        yield Markdown(
            "_Select a challenge from the left panel to view its details._",
            id="detail-markdown",
        )

        with Vertical(id="empty-state"):
            yield Static(
                " _   _  ___    ____  _____ ____  _   _ _   _____ ____\n"
                "| \\ | |/ _ \\  |  _ \\| ____/ ___|| | | | | |_   _/ ___|\n"
                "|  \\| | | | | | |_) |  _| \\___ \\| | | | |   | | \\___ \\\n"
                "| |\\  | |_| | |  _ <| |___ ___) | |_| | |___| |  ___) |\n"
                "|_| \\_|\\___/  |_| \\_\\_____|____/ \\___/|_____|_| |____/",
                id="empty-art",
            )
            yield Static("", id="empty-msg")

    def update_challenge(self, challenge: dict) -> None:
        self.query_one("#session-status", Static).update(
            f"[ ACTIVE_SESSION: {challenge['id']} ]"
        )
        self.query_one("#detail-title", Static).update(
            f"# {challenge['title']}"
        )

        diff_widget = self.query_one("#meta-difficulty-value", Static)
        for cls in ("diff-beginner", "diff-intermediate", "diff-advanced"):
            diff_widget.remove_class(cls)
        diff_widget.update(challenge["difficulty"])
        diff_widget.add_class(difficulty_class(challenge["difficulty"]))

        self.query_one("#meta-category-value", Static).update(challenge["category"])

        objectives = challenge["objectives"]
        for i in range(3):
            obj_widget = self.query_one(f"#obj-{i}", Static)
            if i < len(objectives):
                obj_widget.update(f"[ ]  {objectives[i]}")
                obj_widget.display = True
            else:
                obj_widget.update("")
                obj_widget.styles.display = "none"

        self.query_one("#detail-markdown", Markdown).update(
            challenge.get("markdown", "_No description available._")
        )
        self.scroll_home(animate=False)

    def show_empty_state(self, query: str) -> None:
        for widget_id in ("#session-status", "#detail-title", "#detail-meta", "#objectives-box", "#detail-markdown"):
            self.query_one(widget_id).display = False
        for widget in self.query(".section-heading"):
            widget.display = False

        self.query_one("#empty-msg", Static).update(f'No challenges match "{query}" — try a different keyword.')
        self.query_one("#empty-state").display = True

    def _restore_all(self) -> None:
        self.query_one("#empty-state").display = False
        for widget_id in ("#session-status", "#detail-title", "#detail-meta", "#objectives-box", "#detail-markdown"):
            self.query_one(widget_id).display = True
        for widget in self.query(".section-heading"):
            widget.display = True

