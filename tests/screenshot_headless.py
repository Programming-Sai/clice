"""Headless screenshot harness - works without DISPLAY, without Docker, without termmax.
Run via: python tests/screenshot_headless.py
"""
import asyncio
import inspect
from pathlib import Path
import os

os.environ["TEXTUAL"] = "headless"
# termmax checks this internally - force it to no-op in headless
os.environ["TERMMAX_DISABLED"] = "1"

from ui.main import CliceApp


async def capture(screen_name: str, out_path: Path, size=(140, 40)):
    """Capture one screen headlessly."""
    app = CliceApp()
    async with app.run_test(size=size) as pilot:
        await pilot.pause()
        # Home is already pushed by on_mount, others need explicit push
        if screen_name != "home":
            try:
                # push_screen is sync in textual App, pilot.app variant is same
                pilot.app.push_screen(screen_name)
                await pilot.pause()
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"WARN: could not push {screen_name}: {e}")

        # --- robust save: textual 8.2.7 save_screenshot is SYNC, not async ---
        # It saves SVG even if you name it .png - that's fine, GitHub will still preview SVG as image.
        # We handle both sync and async, and fallback to export_screenshot.
        try:
            target = out_path
            # save_screenshot(filename=..., path=...) is the correct signature
            # Passing full path as filename works, but split to be explicit:
            meth = pilot.app.save_screenshot
            if inspect.iscoroutinefunction(meth):
                result = await meth(str(target))
            else:
                result = meth(str(target))
            print(f"Saved {screen_name} -> {result} (via save_screenshot)")
            # textual writes SVG content even when filename ends .png - ensure file exists
            if not Path(result).exists() and not target.exists():
                raise FileNotFoundError(f"save_screenshot claimed {result} but file missing")
            # If textual returned a different path than requested (e.g. auto dir), copy it
            if Path(result) != target and Path(result).exists():
                Path(result).replace(target)
            return
        except Exception as e:
            print(f"save_screenshot failed for {screen_name}: {e} - trying export_screenshot")

        try:
            svg = pilot.app.export_screenshot()
            out_path.write_text(svg, encoding="utf-8")
            print(f"Saved {screen_name} -> {out_path} (via export_screenshot, {len(svg)} bytes)")
            return
        except Exception as e2:
            print(f"WARN: export_screenshot also failed for {screen_name}: {e2}")
            # create placeholder so artifact upload doesn't warn "no files"
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
        print(f"  {f.name}: {f.stat().st_size} bytes")
    if not files:
        raise SystemExit("ERROR: no screenshots created")


if __name__ == "__main__":
    asyncio.run(main())
