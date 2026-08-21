#!/usr/bin/env python3
"""
clice - CLI Competence Evaluator

    clice                       launch the interactive TUI
    clice list                  list available challenges
    clice run <id>               run a challenge in plain CLI text mode
    clice open <id>              launch the TUI, jumping straight into a challenge
    clice set <key> <value>      change a setting (e.g. set resources.memory 1g)
    clice get <key>              reveal a setting's current value in full
    clice reset [key|all]        revert a setting (or everything) to its default
    clice config                 list every current setting
    clice doctor                 check that Docker/Python/the registry are all OK
    clice update                 update clice to the latest release
    clice uninstall              uninstall clice
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from ui.services.registry import RegistryService
from ui.services.config import Config
from ui.services.settings_schema import (
    FIELDS, KEY_TO_ATTR, cast_and_validate, display_value,
)
from ui.services.utilites import Utilities
from logger.debug import trace
# ChallengeLoader (pulls in docker) and ShellSession (pulls in pexpect) are
# imported lazily inside cmd_run() below - most subcommands (list, set, get,
# reset, config, doctor, --help) never touch a container at all, and both
# of these are comparatively expensive imports to pay on every invocation.


def resolve_challenge(challenges: list, user_input: str) -> dict | None:
    """Match a challenge by exact code, exact full UUID, or a UUID prefix
    of 8+ characters. Shared by both `run` and `open` so they can never
    disagree about what a given id/code actually refers to."""
    for c in challenges:
        code = c.get("code", "")
        uuid_full = c.get("id", "")
        if code == user_input:
            return c
        if uuid_full == user_input:
            return c
        if len(user_input) >= 8 and uuid_full.startswith(user_input):
            return c
    return None


def print_not_found(challenges: list, user_input: str) -> None:
    print(f"Challenge '{user_input}' not found")
    print("\nAvailable challenges:")
    for c in challenges:
        display_id = c.get("code", c.get("id", "???")[:8])
        print(f"  {display_id} - {c.get('title', 'Unknown')}")


# ── list ──────────────────────────────────────────────────────────────

def cmd_list(args, config: Config) -> int:
    registry = RegistryService(config)
    challenges = registry.get_challenges()
    print("\nAvailable challenges:")
    for c in challenges:
        display_id = c.get("code", c.get("id", "???")[:8])
        print(f"  {display_id} - {c.get('title', 'Unknown')} ({c.get('difficulty', 'N/A')})")
    return 0


# ── run ───────────────────────────────────────────────────────────────

def cmd_run(args, config: Config) -> int:
    from loader.challenge_loader import ChallengeLoader
    from logger.session import ShellSession
    from engine.evaluator import evaluate

    trace("cli_run_begin", challenge_id=args.challenge)
    registry = RegistryService(config)
    challenges = registry.get_challenges()
    challenge_info = resolve_challenge(challenges, args.challenge)
    if not challenge_info:
        print_not_found(challenges, args.challenge)
        return 1

    print(f"\n== {challenge_info.get('title', challenge_info.get('code'))} ==")
    print(f"{challenge_info.get('description', 'No description')}\n")

    loader = ChallengeLoader(config)
    try:
        container = None if args.mode == "raw" else loader.load_challenge(challenge_info)
    except KeyboardInterrupt:
        # No container exists yet at this point (or the pull was cut short
        # before one was created) - nothing to clean up, just exit quietly
        # instead of a raw traceback.
        print("\nInterrupted before the environment finished starting up.")
        return 130
    print("✓ Environment ready\n")

    # container_name must be the REAL container's name, or ShellSession
    # silently falls back to spinning up an unrelated, disposable
    # ubuntu:22.04 container - the user's commands would run somewhere
    # completely different from what verify() actually checks afterward.
    container_name = container.name if container else None
    session = ShellSession(challenge_info.get("id"), container_name=container_name)
    session.start()

    print("Type commands. Type ':submit' when done.\n")

    try:
        while True:
            # session.current_prompt is the actual prompt captured from
            # inside the container (e.g. "root@abc123:/workspace$"), kept
            # up to date by execute() after every command - using it here
            # instead of a static "$ " is what makes this look and behave
            # like a real terminal rather than a debug harness.
            cmd = input(f"{session.current_prompt} ").strip()
            if not cmd:
                continue
            if cmd == ":submit":
                break
            if cmd == ":quit":
                print("Session cancelled")
                loader.cleanup(container)
                return 0

            output, exit_code, elapsed, prompt = session.execute(cmd)
            # No timing, no exit-code annotation, no "======" framing - a
            # real shell doesn't announce any of that after a plain
            # command, it just shows the output. session.commands still
            # tracks exit_code/elapsed internally for scoring regardless
            # of what gets printed here.
            if output:
                print(output)
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C at the prompt, or stdin closing unexpectedly (e.g. piped
        # input running out) - without this, either would propagate straight
        # up and skip cleanup() entirely, orphaning the container.
        print("\nInterrupted - cleaning up...")
        loader.cleanup(container)
        return 130

    log = session.submit()

    print("\nVerifying...")
    verify_result = loader.verify(challenge_info.get("id"), container)
    passed = verify_result["passed"]

    log["goal_reached"] = passed
    log["checker_output"] = verify_result["output"]
    log["checker_exit_code"] = verify_result["exit_code"]
    log["checker_error"] = verify_result["error"]
    metrics = evaluate(log)

    safe_timestamp = log["started_at"].replace(":", "-")
    log_path = Path("assets") / f"{challenge_info.get('id')}_{safe_timestamp}.json"
    log_path.parent.mkdir(exist_ok=True)
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)

    print("\n" + "=" * 50)
    print("RESULTS")
    print("=" * 50)
    if verify_result["error"]:
        print(f"Challenge: ⚠ ENVIRONMENT ERROR - {verify_result['error']}")
    else:
        print(f"Challenge: {'✓ PASSED' if passed else '✗ FAILED'}")
    print(f"Commands: {metrics['command_count']}")
    print(f"Time: {metrics['time_seconds']:.1f}s")
    print(f"Error rate: {metrics['error_rate']:.0f}%")
    print(f"Log saved: {log_path}")

    loader.cleanup(container)
    return 0 if passed else 1


# ── open ──────────────────────────────────────────────────────────────

def cmd_open(args, config: Config) -> int:
    """Launch the full TUI, skipping Home/Browser, straight into this
    challenge's session screen."""
    registry = RegistryService(config)
    challenges = registry.get_challenges()
    challenge_info = resolve_challenge(challenges, args.challenge)
    if not challenge_info:
        print_not_found(challenges, args.challenge)
        return 1

    from ui.main import run as run_tui
    run_tui(initial_challenge=challenge_info)
    return 0


# ── settings: set / get / reset / config ────────────────────────────────

def cmd_set(args, config: Config) -> int:
    key = args.key.lower()
    attr = KEY_TO_ATTR.get(key)
    if attr is None:
        print(f"Unknown setting '{key}'. Run `clice config` to see valid keys.")
        return 1
    try:
        value = cast_and_validate(attr, args.value)
    except ValueError as e:
        print(f"Invalid value for '{key}': {e}")
        return 1
    config.save(**{attr: value})
    print(f"Saved {key} = {display_value(attr, value)}")
    return 0


def cmd_get(args, config: Config) -> int:
    key = args.key.lower()
    attr = KEY_TO_ATTR.get(key)
    if attr is None:
        print(f"Unknown setting '{key}'. Run `clice config` to see valid keys.")
        return 1
    value = getattr(config, attr)
    print(f"{key} = {value if value not in (None, '') else '(not set)'}")
    return 0


def cmd_reset(args, config: Config) -> int:
    if args.key is None or args.key.lower() == "all":
        config.reset()
        print("All settings reset to defaults.")
        return 0
    key = args.key.lower()
    attr = KEY_TO_ATTR.get(key)
    if attr is None:
        print(f"Unknown setting '{key}'. Run `clice config` to see valid keys.")
        return 1
    config.reset(attr)
    print(f"Reset {key} to default.")
    return 0


def cmd_config(args, config: Config) -> int:
    print(f"{'KEY':<26} {'VALUE':<20} DESCRIPTION")
    print("-" * 80)
    for key, attr, description in FIELDS:
        value = getattr(config, attr)
        print(f"{key:<26} {display_value(attr, value):<20} {description}")
    return 0


# ── doctor ────────────────────────────────────────────────────────────

# ── update / uninstall ───────────────────────────────────────────────

_INSTALL_SCRIPT_URL = "https://raw.githubusercontent.com/programming-sai/clice/main/install.sh"
_UNINSTALL_SCRIPT_URL = "https://raw.githubusercontent.com/programming-sai/clice/main/uninstall.sh"


def _fetch_and_run_script(url: str, script_args: list[str]) -> int:
    """Download a shell script and run it via bash, streaming its output
    live (not captured) so interactive prompts and colored output work
    exactly as they would running it directly. Runs the real, single
    source of truth (install.sh / uninstall.sh) rather than reimplementing
    their logic here - the two can never drift apart."""
    import requests

    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"Failed to fetch {url}: {e}")
        return 1

    with tempfile.NamedTemporaryFile(mode="w", suffix=".sh", delete=False) as f:
        f.write(response.text)
        script_path = f.name

    try:
        result = subprocess.run(["bash", script_path, *script_args])
        return result.returncode
    finally:
        Path(script_path).unlink(missing_ok=True)


def cmd_update(args, config: Config) -> int:
    is_frozen = getattr(sys, "frozen", False)
    if not is_frozen:
        print("Note: this is a source install (pip install -e .) - 'update' only")
        print("affects the separately-installed release binary in ~/.clice/app,")
        print("not this dev environment. Use 'git pull' to update your source checkout.\n")

    script_args = []
    if args.with_docker:
        script_args.append("--with-docker")
    if args.no_docker:
        script_args.append("--no-docker")

    print("Fetching the latest install script...")
    code = _fetch_and_run_script(_INSTALL_SCRIPT_URL, script_args)
    if code == 0 and is_frozen:
        print("\nUpdate complete. Since this replaces the binary on disk (not the")
        print("copy already running), the new version takes effect the next time")
        print("you run clice - not this current invocation.")
    return code


def cmd_uninstall(args, config: Config) -> int:
    if not args.yes:
        reply = input("This will remove clice and its local data. Continue? [y/N] ").strip().lower()
        if reply not in ("y", "yes"):
            print("Cancelled.")
            return 0

    script_args = []
    if args.keep_settings:
        script_args.append("--keep-settings")

    return _fetch_and_run_script(_UNINSTALL_SCRIPT_URL, script_args)


def cmd_doctor(args, config: Config) -> int:
    ok = True

    print("clice doctor\n")

    py_version = sys.version_info
    is_frozen = getattr(sys, "frozen", False)
    if not is_frozen:
        # Only meaningful for a source install (pip install -e .) - the
        # frozen binary bundles its own interpreter and never touches
        # system Python at all, so there's nothing here worth reporting
        # in that case; omitting it keeps doctor's output honest about
        # Docker being the only real external dependency.
        py_ok = py_version >= (3, 10)
        print(f"[{'OK' if py_ok else 'FAIL'}] Python {py_version.major}.{py_version.minor}.{py_version.micro} "
              f"({'>= 3.10 required' if not py_ok else 'meets minimum'})")
        ok = ok and py_ok

    docker_status = Utilities().get_docker_status(force=True)
    docker_ok = docker_status.get("status") == "ok"
    print(f"[{'OK' if docker_ok else 'FAIL'}] Docker: {docker_status.get('message', 'unknown')}")
    ok = ok and docker_ok

    try:
        registry = RegistryService(config)
        challenges = registry.get_challenges()
        synced = registry.is_synced()
        print(f"[OK] Registry reachable - {len(challenges)} challenge(s), "
              f"{'in sync' if synced else 'local cache differs from remote'}")
    except Exception as e:
        print(f"[FAIL] Registry unreachable: {e}")
        ok = False

    try:
        config.cache_dir.mkdir(parents=True, exist_ok=True)
        test_file = config.cache_dir / ".doctor_write_test"
        test_file.write_text("ok")
        test_file.unlink()
        print(f"[OK] Cache directory writable ({config.cache_dir})")
    except OSError as e:
        print(f"[FAIL] Cache directory not writable ({config.cache_dir}): {e}")
        ok = False

    print(f"\n{'Everything looks good.' if ok else 'One or more checks failed - see above.'}")
    return 0 if ok else 1


# ── direct screen launchers ──────────────────────────────────────────

def _launch_screen(screen_name: str) -> int:
    from ui.main import run as run_tui
    run_tui(initial_screen=screen_name)
    return 0


def cmd_history(args, config: Config) -> int:
    return _launch_screen("history")


def cmd_settings(args, config: Config) -> int:
    return _launch_screen("settings")


def cmd_browser(args, config: Config) -> int:
    return _launch_screen("browser")


# ── entry point ──────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="clice", description="CLI Competence Evaluator")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List available challenges")

    p_run = sub.add_parser("run", help="Run a challenge in plain CLI text mode")
    p_run.add_argument("challenge", help="Challenge id, code, or UUID prefix")
    p_run.add_argument("mode", nargs="?", default="container", help="'container' (default) or 'raw'")

    p_open = sub.add_parser("open", help="Launch the TUI directly into a challenge")
    p_open.add_argument("challenge", help="Challenge id, code, or UUID prefix")

    p_set = sub.add_parser("set", help="Change a setting")
    p_set.add_argument("key")
    p_set.add_argument("value")

    p_get = sub.add_parser("get", help="Reveal a setting's current value")
    p_get.add_argument("key")

    p_reset = sub.add_parser("reset", help="Reset a setting (or 'all') to default")
    p_reset.add_argument("key", nargs="?", default=None)

    sub.add_parser("config", help="List all current settings")
    sub.add_parser("doctor", help="Check that Docker/Python/the registry are all OK")

    p_update = sub.add_parser("update", help="Update clice to the latest release")
    p_update.add_argument("--with-docker", action="store_true", help="Auto-install Docker if missing, no prompt")
    p_update.add_argument("--no-docker", action="store_true", help="Never install Docker, no prompt")

    p_uninstall = sub.add_parser("uninstall", help="Uninstall clice")
    p_uninstall.add_argument("--keep-settings", action="store_true", help="Keep settings.json and history")
    p_uninstall.add_argument("-y", "--yes", action="store_true", help="Skip the confirmation prompt")
    sub.add_parser("history", help="Launch the TUI directly into History")
    sub.add_parser("settings", help="Launch the TUI directly into Settings")
    sub.add_parser("browser", help="Launch the TUI directly into the Browser")

    return parser


COMMANDS = {
    "list": cmd_list,
    "run": cmd_run,
    "open": cmd_open,
    "set": cmd_set,
    "get": cmd_get,
    "reset": cmd_reset,
    "config": cmd_config,
    "doctor": cmd_doctor,
    "update": cmd_update,
    "uninstall": cmd_uninstall,
    "history": cmd_history,
    "settings": cmd_settings,
    "browser": cmd_browser,
}


def main():
    trace("cli_main_begin", argv=sys.argv[1:])
    parser = build_parser()
    args = parser.parse_args()

    if args.command is None:
        # No subcommand at all - launch the interactive TUI, same as
        # just running `clice` with nothing else.
        from ui.main import run as run_tui
        run_tui()
        return

    config = Config()
    handler = COMMANDS[args.command]
    sys.exit(handler(args, config))


if __name__ == "__main__":
    main()