"""Headless screenshot harness - works without DISPLAY, without Docker, without termmax.
Run via: PYTHONPATH=. python tests/screenshot_headless.py
"""
import asyncio
import inspect
import sys
from pathlib import Path

# --- FIX 1: allow `python tests/screenshot_headless.py` to find `ui` ---
# When run as `python tests/foo.py`, sys.path[0] is .../tests, not repo root.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import os
os.environ["TEXTUAL"] = "headless"
os.environ["TERMMAX_DISABLED"] = "1"

from textual.widgets import Static  # for polling placeholders
from ui.main import CliceApp


async def wait_for_home_ready(pilot, timeout=8.0):
    """Wait until HomeScreen's [...] placeholders are replaced.
    HomeScreen._do_refresh runs in a thread and replaces [...] with SYNCED/ERROR etc.
    If we screenshot too early we get empty [...] state.
    We poll for that text; if still there after timeout we screenshot anyway (better than empty failure).
    """
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        await pilot.pause()
        try:
            # Any Static still showing [...] means refresh hasn't finished
            placeholders = []
            for w in pilot.app.query(Static):
                try:
                    # Static stores renderable in .renderable or ._renderable
                    txt = ""
                    if hasattr(w, "renderable") and w.renderable is not None:
                        txt = str(w.renderable)
                    elif hasattr(w, "_renderable") and w._renderable is not None:
                        txt = str(w._renderable)
                    else:
                        # fallback: render the widget
                        txt = str(w.render())
                    if "[...]" in txt:
                        placeholders.append(w)
                except Exception:
                    continue
            if not placeholders:
                # also give compositor a final frame
                await asyncio.sleep(0.3)
                return True
        except Exception:
            pass
        await asyncio.sleep(0.5)
    print(f"WARN: wait_for_home_ready timed out after {timeout}s - screenshotting anyway")
    return False


async def capture(screen_name: str, out_path: Path, size=(140, 42)):
    app = CliceApp()
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        # Let initial mount + termmax no-op settle
        await asyncio.sleep(0.5)

        if screen_name != "home":
            try:
                pilot.app.push_screen(screen_name)
                await pilot.pause()
                await asyncio.sleep(0.8)
            except Exception as e:
                print(f"WARN: could not push {screen_name}: {e}")

        # For home, wait for background thread to replace [...] 
        if screen_name == "home":
            await wait_for_home_ready(pilot, timeout=7)
        else:
            # browser/history/settings also do async loads (registry, history scans)
            # give them a moment
            await pilot.pause()
            await asyncio.sleep(1.2)

        # Final idle
        await pilot.pause()
        await asyncio.sleep(0.5)

        # --- robust save: textual 8.2.7 save_screenshot is SYNC, not async ---
        try:
            meth = pilot.app.save_screenshot
            if inspect.iscoroutinefunction(meth):
                result = await meth(str(out_path))
            else:
                result = meth(str(out_path))
            print(f"Saved {screen_name} -> {result} (via save_screenshot)")
            # textual joins path internally; ensure requested file exists
            result_path = Path(result)
            if result_path != out_path and result_path.exists():
                # move to expected name if textual auto-named differently
                result_path.replace(out_path)
                print(f"  moved {result_path} -> {out_path}")
            elif not out_path.exists() and result_path.exists():
                # already at right place
                pass
            if out_path.exists():
                return
            else:
                raise FileNotFoundError(f"save_screenshot returned {result} but {out_path} missing")
        except Exception as e:
            print(f"save_screenshot failed for {screen_name}: {e} - trying export_screenshot")

        try:
            svg = pilot.app.export_screenshot()
            out_path.write_text(svg, encoding="utf-8")
            print(f"Saved {screen_name} -> {out_path} (via export_screenshot, {len(svg)} bytes)")
            return
        except Exception as e2:
            print(f"WARN: export_screenshot also failed for {screen_name}: {e2}")
            try:
                out_path.write_text(f"<svg><!-- placeholder for {screen_name} failed: {e2} --></svg>", encoding="utf-8")
            except Exception:
                out_path.touch()
            print(f"Created placeholder {out_path}")


async def main():
    out_dir = Path("screenshots")
    out_dir.mkdir(exist_ok=True, parents=True)
    # clean old
    for p in out_dir.glob("*"):
        try:
            p.unlink()
        except Exception:
            pass

    await capture("home", out_dir / "Home-Screen.png")
    await capture("browser", out_dir / "Browser.png")
    await capture("history", out_dir / "History-Screen.png")
    await capture("settings", out_dir / "Settings-Screen.png")

    files = list(out_dir.glob("*"))
    print(f"All screenshots done: {files}")
    for f in files:
        try:
            print(f"  {f.name}: {f.stat().st_size} bytes")
        except Exception:
            print(f"  {f.name}: ? bytes")
    if not files:
        raise SystemExit("ERROR: no screenshots created")


if __name__ == "__main__":
    asyncio.run(main())
