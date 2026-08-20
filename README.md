# clice

**CLI Competence Evaluator** — a sandboxed terminal-challenge platform. Pull a
challenge, work inside an isolated Docker container, get graded automatically,
optionally get AI feedback on your approach.

Think of it as a self-hosted, terminal-native "practice your CLI skills"
tool — beginner file-manipulation exercises up through advanced
process/networking challenges, all run in disposable containers so nothing
you do can touch your actual machine.

---

## Requirements

- **Linux, macOS, or WSL.** No native Windows support — clice uses `pexpect`
  under the hood for real interactive shell sessions, which has no
  equivalent outside a real Unix environment.
- **Docker**, installed and running. This is the only real external
  dependency — the app itself ships as a single self-contained binary with
  no other prerequisites.

## Install

```bash
curl -fsSL https://raw.githubusercontent.com/programming-sai/clice/main/install.sh | bash
```

This detects your platform, checks for Docker (and — on Linux, only if you
say yes — offers to install it for you via Docker's own official script),
downloads the right binary, and puts `clice` on your `PATH`.

If it's your first time and `~/.local/bin` wasn't already on your `PATH`,
open a new terminal (or `source` your shell's rc file, as the installer
will tell you) before `clice` is found.

**Confirm it worked:**

```bash
clice doctor
```

This checks Docker, the challenge registry, and your local cache directory,
and tells you plainly if anything's wrong before you try to actually use it.

## Quick start

```bash
clice list              # see what challenges are available
clice open hello-clice  # launch the full TUI, straight into a challenge
```

Or skip the TUI entirely and work in a plain terminal:

```bash
clice run hello-clice
```

Type commands at the `$` prompt, type `:submit` when you're done, `:quit` to
bail out early.

Or just run `clice` on its own for the full interactive app — home screen,
challenge browser, history, and settings.

---

## AI feedback (optional, but worth setting up)

After you submit a challenge, clice can generate a written breakdown of your
approach — what you did well, what you missed, why the checker passed or
failed you — using an LLM. **This is entirely optional.** Without it
configured, clice still works completely normally: verification, scoring,
and the pass/fail verdict are all independent of this and never require an
API key. You'll just see a note that AI feedback isn't available instead of
the written breakdown.

To turn it on, you need:

1. **An OpenRouter API key.** clice talks to [OpenRouter](https://openrouter.ai),
   which is an OpenAI-compatible gateway in front of a large number of
   models from different providers — so "OpenRouter key" and "OpenAI-compatible
   model" are really the same requirement here, not two separate things.
   Sign up at openrouter.ai and grab a key from
   [openrouter.ai/keys](https://openrouter.ai/keys).
2. **A model name** — any valid OpenRouter model slug. OpenRouter has
   genuinely free-tier models available (clice's own default is
   `deepseek/deepseek-chat-v3-0324:free`), so this doesn't have to cost
   anything to try.

Set both:

```bash
clice set ai.api_key sk-or-...your-key-here
clice set ai.model deepseek/deepseek-chat-v3-0324:free
```

Confirm it's set (the key is masked, shown only as its last few characters,
in normal listings — `get` shows it in full if you ever need to check it):

```bash
clice config
clice get ai.api_key
```

That's it — the next challenge you submit will include AI feedback
automatically.

---

## Command reference

| Command                             | What it does                                                           |
| ----------------------------------- | ---------------------------------------------------------------------- |
| `clice`                             | Launch the full interactive TUI (Home screen)                          |
| `clice list`                        | List all available challenges                                          |
| `clice open <id>`                   | Launch the TUI directly into a specific challenge, skipping navigation |
| `clice run <id>`                    | Run a challenge in plain-text CLI mode (no TUI)                        |
| `clice browser`                     | Launch the TUI directly into the challenge browser                     |
| `clice history`                     | Launch the TUI directly into your session history                      |
| `clice settings`                    | Launch the TUI directly into the settings screen                       |
| `clice config`                      | Print every current setting and its value                              |
| `clice get <key>`                   | Print one setting's value in full (unmasks the API key)                |
| `clice set <key> <value>`           | Change a setting                                                       |
| `clice reset <key>` / `clice reset` | Revert one setting (or everything) to its default                      |
| `clice doctor`                      | Check Docker, the registry, and your local setup                       |

`<id>` accepts a challenge's short code (`hello-clice`), its full UUID, or
an 8+ character prefix of that UUID.

## Settings reference

| Key                         | Default                               | What it controls                                                             |
| --------------------------- | ------------------------------------- | ---------------------------------------------------------------------------- |
| `resources.memory`          | `512m`                                | Memory limit for the challenge container (Docker format: `512m`, `1g`, etc.) |
| `resources.cpu_cores`       | `1.0`                                 | CPU cores allocated to the challenge container                               |
| `resources.checker_timeout` | `20`                                  | Seconds before a hung/slow checker script is killed                          |
| `resources.docker_timeout`  | `30`                                  | Seconds before a stalled image pull is given up on                           |
| `behaviour.network`         | `on`                                  | Whether challenge containers get network access                              |
| `behaviour.auto_cleanup`    | `on`                                  | Whether containers are removed automatically after a session                 |
| `ai.model`                  | `deepseek/deepseek-chat-v3-0324:free` | Model used for AI feedback                                                   |
| `ai.api_key`                | _(not set)_                           | Your OpenRouter API key                                                      |
| `ai.max_tokens`             | `800`                                 | Max length of the AI feedback response                                       |

All of this lives in `~/.clice/settings.json`, created the first time you
change anything — it only ever stores what you've actually changed, layered
on top of built-in defaults. Deleting that file (or `clice reset` with no
argument) puts everything back to defaults.

Inside the TUI's own settings screen, the same keys work via a small
command line: `set <key> <value>`, `get <key>`, `reset <key>`, `reset all`,
`undo` (steps back through your last change), `help`.

---

## Using the TUI

| Key | Screen                               |
| --- | ------------------------------------ |
| `x` | Home                                 |
| `b` | Browser (all challenges, searchable) |
| `h` | History (past sessions, searchable)  |
| `s` | Settings                             |
| `q` | Quit                                 |

**Browser search** supports plain substring matching (`title:login`),
regex (`title:/^failed/`), and shortcuts like `:pass` / `:fail` for status.
Same syntax in History.

**Inside a challenge session**: work normally in the shell, then submit
with the keybinding shown in the footer. You'll land on a verdict screen —
PASS (green), FAIL (red), or ENVIRONMENT ERROR (amber, meaning the checker
itself couldn't run — a real distinction from actually getting the
challenge wrong). If AI feedback is loading, `r` retries it if it fails or
times out.

---

## Challenges

Run `clice list` for the current set — difficulty ranges from beginner
(single-command file tasks) through advanced (multi-step system
administration: users, permissions, live process/network state, no fixed
file to check). New challenges live in a
[separate repo](https://github.com/programming-sai/clice-challenges) and
get pulled in automatically; you don't need to do anything to get new ones
as they're added.

---

## Troubleshooting

**`clice: command not found` right after installing** — open a new
terminal, or run the `source ~/.bashrc` (or `.zshrc`) line the installer
printed. This is a normal shell limitation, not a bug: a script can't
modify the `PATH` of the terminal session that's already running it.

**`clice doctor` shows `Docker: NOT CONNECTED` right after the installer
set up Docker for you** — you need to `newgrp docker` or open a new
terminal for the group-membership change to take effect. Also expected,
not a bug.

**Everything feels slow the first time you open a challenge** — that's a
real image pull (Docker downloading the challenge's container image),
which only happens once per challenge; subsequent runs reuse the cached
image and are much faster.

**AI feedback says "not available" or shows an error** — either you haven't
set `ai.api_key` yet (see the AI feedback section above), or OpenRouter
rejected the key/model — `clice get ai.api_key` and `clice get ai.model`
to double check what's actually configured.

Anything else: `clice doctor` first, it catches most of the common issues
directly.

## Uninstalling

```bash
rm -rf ~/.clice ~/.local/bin/clice
```

That's everything — the binary, the settings, the local challenge cache,
and your session history. Nothing else on your system is touched.
