import os
import sys

from textual.app import App

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ui.screens.session import SessionScreen


class DummyContainer:
    name = "clice-test"
    id = "dummy-id"


class ProbeApp(App):
    def on_mount(self) -> None:
        self.push_screen(SessionScreen({"id": "test_01", "title": "Test"}, True, True, DummyContainer()))
        self.set_timer(3, self.exit)


def main() -> None:
    ProbeApp().run(headless=True)


if __name__ == "__main__":
    main()
