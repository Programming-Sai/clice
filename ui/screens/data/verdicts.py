# ══════════════════════════════════════════════════════════════════════════════
#  📝 VERDICT MARKDOWN  —  one string per scenario
# ══════════════════════════════════════════════════════════════════════════════
#
# VERDICT_MD_PASS  shown when IS_PASSING = True  (green screen)
# VERDICT_MD_FAIL  shown when IS_PASSING = False (red screen)
#
# These are full Markdown strings. Textual's Markdown widget renders them with
# real formatting: bold, italics, tables, code fences, bullet lists.



VERDICT_MD_PASS = """\
## ✅ Session Validated

All environment assertions returned **EXIT_CODE(0)**. The submission adheres
to the structural integrity constraints defined in `CLICE_CORE_v4.2`.
Optimization thresholds were met with a **12 % margin**.

### What You Demonstrated

- Correct octal permission bits on `/etc/shadow` (`640`)
- Recursive ownership change on the web root using `find … -exec`
- `umask 027` configured for the shared group directory with `g+s`

### Score Breakdown

| Check | Result |
|-------|--------|
| `/etc/shadow` permissions | ✅ PASS |
| Web root ownership | ✅ PASS |
| umask + setgid bit | ✅ PASS |

> **Next challenge:** `CH-02 — SUDOERS_HARDENING`
"""

VERDICT_MD_FAIL = """\
## ❌ Session Failed

One or more environment assertions returned **EXIT_CODE(1)**. Review the
failed checks below and resubmit.

### Failed Checks

| Check | Result | Hint |
|-------|--------|------|
| `/etc/shadow` permissions | ❌ FAIL | Expected `640`, got `644` — world-readable! |
| Web root ownership | ❌ FAIL | `chown -R` used directly; use `find … -exec` |
| umask + setgid bit | ✅ PASS | — |

### Reminder: Core Concepts

`chmod` octal digit = **4** (read) + **2** (write) + **1** (execute).

```bash
chmod 640 /etc/shadow
find /var/www -exec chown www-data:www-data {} +
```

> Re-run `./scripts/validate_integrity.sh` after each fix.
"""

# The one we'll actually render, chosen by the master switch


# ── Timeline log rows ─────────────────────────────────────────────────────────
# Each tuple: (timestamp, command, exit_code_string)

# TIMELINE_ROWS = [
#     ("[14:20:01]", "systemctl status clice-daemon",         f"({'0' if IS_PASSING else '1'})"),
#     ("[14:20:15]", "ls -la /var/log/clice/",                f"({'0' if IS_PASSING else '1'})"),
#     ("[14:20:45]", "sed -i 's/DEBUG/INFO/g' config.yaml",   f"({'0' if IS_PASSING else '1'})"),
#     ("[14:21:10]", 'grep -r "CRITICAL" ./src',              f"({'0' if IS_PASSING else '1'})"),
#     ("[14:22:05]", "./scripts/validate_integrity.sh",       f"({'0' if IS_PASSING else '1'})"),
#     ("[14:23:30]", "curl -X POST localhost:8080/v1/submit",  f"({'0' if IS_PASSING else '1'})"),
#     ("[14:24:00]", "rm -rf ./tmp/*",                        f"({'0' if IS_PASSING else '1'})"),
#     ("[14:24:12]", 'echo "SUBMISSION_COMPLETE"',             f"({'0' if IS_PASSING else '1'})"),
# ]

