# ui/widgets/challenges/search_input.py

from textual.widgets import Input

class SearchInput(Input):
    def _on_key(self, event) -> None:
        if event.key in ("up", "down", "alt+x"):
            event.prevent_default()
            event.stop()
            # bubble it up to the screen's on_key
            self.screen.on_key(event)
            return
        super()._on_key(event)