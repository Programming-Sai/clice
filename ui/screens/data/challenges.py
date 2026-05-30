CHALLENGES = [
    {
        "id": "CH-01",
        "title": "FILE_PERMISSIONS",
        "tags": ["CHMOD", "CHOWN", "UMASK"],
        "difficulty": "BEGINNER [#--]",
        "category": "FILESYSTEM",
        "description": (
            "Master the Unix permission model. Learn how to read, set, and "
            "audit file permissions using chmod, chown, and umask. Understand "
            "octal notation and symbolic modes."
        ),
        "objectives": [
            "Set correct permissions on /etc/shadow",
            "Change ownership of a web root recursively",
            "Configure umask for a shared group directory",
        ],
        "markdown": """\
## Overview

Every file and directory in Unix carries a **permission bitmask** split across
three principals: *owner*, *group*, and *other*. Reading that mask correctly is
the first skill any sysadmin must internalize.

## Core Tools

| Tool | Purpose |
|------|---------|
| `chmod` | Change the permission bits of a file or directory |
| `chown` | Change the owning user and/or group |
| `umask` | Set the default permission mask for newly created files |

## Octal vs Symbolic Modes

`chmod` accepts two notations:

```bash
# Octal — three digits, each 0-7
chmod 640 /etc/shadow        # owner=rw, group=r, other=none

# Symbolic — easier to read incrementally
chmod u=rw,g=r,o= /etc/shadow
chmod +x deploy.sh           # add execute for everyone
```

The octal digit is just the sum of **4** (read) + **2** (write) + **1** (execute).

## umask

`umask` is subtracted from the default creation mode (`0666` for files,
`0777` for directories):

```bash
umask 027   # files → 640, dirs → 750
umask       # print current mask
```

A shared-group directory usually wants `g+s` (setgid bit) so new files
inherit the group:

```bash
chmod 2775 /srv/shared
```

## Tips & Gotchas

- `/etc/shadow` **must** be `640` or `000`; world-readable shadow files are a critical vuln.
- Recursive `chown` with `-R` on a live web root can break running processes — prefer `find … -exec`.
- `stat -c '%a %n' <file>` prints the octal mode — handy in scripts.
""",
    },
    {
        "id": "CH-02",
        "title": "SED_WIZARDRY",
        "tags": ["STREAM_EDITING", "REGEX"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "DATA_STREAMS",
        "description": (
            "Learn the dark arts of stream editing. You will be tasked with "
            "transforming massive unstructured logs into surgical reports using "
            "only 'sed'. Master the address range, pattern space, and hold "
            "space. This challenge focuses on non-destructive data manipulation "
            "and complex regex substitution patterns."
        ),
        "objectives": [
            "Parse /var/log/syslog for auth failures",
            "Inject timestamp headers every 50 lines",
            "Anonymize IP addresses using patterns",
        ],
        "markdown": """\
## Overview

`sed` (Stream EDitor) processes text line by line, applying a *script* of
editing commands. It is the scalpel of Unix text processing — precise,
non-destructive, and composable with pipes.

## Address Ranges

Commands can be targeted with **addresses** before them:

```bash
sed '10,20d'        file   # delete lines 10-20
sed '/ERROR/,/END/p' file  # print from ERROR to END (inclusive)
sed '0~50s/^/---\n/' file  # every 50th line, prepend a separator
```

## The Pattern Space & Hold Space

`sed` maintains two buffers:

| Buffer | Purpose |
|--------|---------|
| **Pattern space** | The current line being processed |
| **Hold space** | A scratchpad you control manually |

Key commands: `h` (copy pattern→hold), `g` (copy hold→pattern), `x` (swap),
`H`/`G` (append versions).

## Substitution Deep Dive

```bash
# Basic substitution
sed 's/foo/bar/'          # first match per line
sed 's/foo/bar/g'         # all matches per line

# Capture groups (BRE — use \\( \\))
sed 's/\\([0-9]\\{1,3\\}\\.\\)\\{3\\}[0-9]\\{1,3\\}/[REDACTED]/g'

# ERE with -E — cleaner syntax
sed -E 's/([0-9]{1,3}\\.){3}[0-9]{1,3}/[REDACTED]/g'
```

## Practical Recipes

```bash
# Extract auth failures from syslog
sed -n '/authentication failure/p' /var/log/syslog

# Inject a header every 50 lines
sed '0~50i\\--- BLOCK BOUNDARY ---' /var/log/app.log

# Anonymize IPv4 addresses
sed -E 's/([0-9]{1,3}\\.){3}[0-9]{1,3}/[IP_REDACTED]/g' access.log
```

## Tips & Gotchas

- `-n` suppresses automatic printing; pair with `p` to print only matches.
- `-i` edits **in place** — always test without it first or use `-i.bak`.
- GNU sed and BSD sed differ in syntax for in-place editing: `-i ''` on macOS.
""",
    },
    {
        "id": "CH-03",
        "title": "PROCESS_SIGNALS",
        "tags": ["SIGTERM", "SIGKILL", "TRAP"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "PROCESS_MGMT",
        "description": (
            "Explore Unix process signals and how programs respond to them. "
            "Write signal handlers, gracefully stop services, and trap "
            "interrupts in shell scripts."
        ),
        "objectives": [
            "Send SIGTERM to a running daemon",
            "Trap SIGINT in a bash script",
            "Verify process cleanup after SIGKILL",
        ],
        "markdown": """\
## Overview

Signals are the Unix mechanism for asynchronous inter-process communication.
Every running process can **send**, **receive**, **handle**, or **ignore** them
(with one exception: `SIGKILL` cannot be caught or ignored).

## Common Signals

| Signal | Number | Default Action | Notes |
|--------|--------|---------------|-------|
| `SIGHUP` | 1 | Terminate | Reload config in daemons |
| `SIGINT` | 2 | Terminate | Ctrl+C from terminal |
| `SIGQUIT` | 3 | Core dump | Ctrl+\\ |
| `SIGTERM` | 15 | Terminate | Polite shutdown request |
| `SIGKILL` | 9 | Terminate | Cannot be caught |
| `SIGCHLD` | 17 | Ignore | Child stopped or exited |

## Sending Signals

```bash
kill -TERM <pid>       # polite stop (default if no signal given)
kill -9 <pid>          # force kill — no cleanup possible
kill -HUP <pid>        # ask daemon to reload config
killall -TERM nginx    # target by name
pkill -f 'python app'  # match against full command line
```

## Trapping Signals in Bash

```bash
#!/usr/bin/env bash

cleanup() {
    echo "Caught signal — cleaning up temp files..."
    rm -f /tmp/myapp_*.lock
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Running... (PID $$)"
while true; do sleep 1; done
```

## Verifying Cleanup After SIGKILL

```bash
# Before
ps aux | grep myapp

# Send SIGKILL
kill -9 <pid>

# Check for zombies or leftover resources
ps aux | grep myapp
ls /proc/<pid>          # should be gone
lsof -p <pid>           # open files (should error)
```

## Tips & Gotchas

- Always try `SIGTERM` before `SIGKILL` — give the process a chance to clean up.
- `trap '' SIGINT` inside a script prevents Ctrl+C from killing it (useful for critical sections).
- Zombie processes (`Z` state in `ps`) mean the parent never called `wait()` — kill the parent to adopt them to init.
""",
    },
    {
        "id": "CH-04",
        "title": "NETWORK_PLUMBING",
        "tags": ["NC", "IPTABLES", "ROUTES"],
        "difficulty": "ADVANCED [###]",
        "category": "NETWORKING",
        "description": (
            "Become a network plumber. Use netcat, iptables, and ip route to "
            "build, inspect, and filter traffic flows. Understand packet "
            "traversal and NAT rules."
        ),
        "objectives": [
            "Open a TCP listener with netcat",
            "Block an IP with an iptables DROP rule",
            "Add a static route to an isolated subnet",
        ],
        "markdown": """\
## Overview

Network plumbing means understanding and controlling how packets flow through
your system — from raw socket listeners all the way to kernel-level filtering
and routing decisions.

## netcat (`nc`) — The TCP Swiss Army Knife

```bash
# Listen on port 4444 (server)
nc -lvp 4444

# Connect to a listener (client)
nc 192.168.1.10 4444

# Transfer a file
nc -lvp 4444 > received.tar.gz          # receiver
tar czf - /data | nc 192.168.1.10 4444  # sender

# Port scan (no -z on older nc; use nmap for real scans)
nc -zv 10.0.0.1 20-25
```

## iptables — Packet Filtering

The **filter** table has three built-in chains: `INPUT`, `FORWARD`, `OUTPUT`.

```bash
# Block all traffic from an IP (INPUT chain)
iptables -A INPUT -s 203.0.113.42 -j DROP

# Allow established connections
iptables -A INPUT -m state --state ESTABLISHED,RELATED -j ACCEPT

# NAT masquerade (share internet via this host)
iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE

# List rules with line numbers
iptables -L INPUT -n --line-numbers

# Delete rule by line number
iptables -D INPUT 3
```

> **Warning:** `iptables -F` flushes ALL rules. On a remote server this can
> lock you out. Use `iptables-restore` with a saved ruleset for safety.

## ip route — Static Routing

```bash
# View routing table
ip route show

# Add a static route
ip route add 10.20.0.0/24 via 192.168.1.1 dev eth0

# Delete a route
ip route del 10.20.0.0/24

# Persist across reboots (Debian/Ubuntu)
echo 'up ip route add 10.20.0.0/24 via 192.168.1.1' >> /etc/network/interfaces
```

## Tips & Gotchas

- Enable IP forwarding before setting up NAT: `echo 1 > /proc/sys/net/ipv4/ip_forward`
- `nftables` is the modern replacement for `iptables` on newer kernels — same concepts, cleaner syntax.
- Use `tcpdump -i any -n port 4444` to watch your netcat traffic live.
""",
    },
    {
        "id": "CH-05",
        "title": "ZOMBIE_HUNTING",
        "tags": ["PID", "PPID", "FORK"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "PROCESS_MGMT",
        "description": (
            "Track down and eliminate zombie processes. Learn how fork() "
            "creates child processes, why they become zombies when the parent "
            "ignores them, and how to reap them properly."
        ),
        "objectives": [
            "Identify zombie processes with ps",
            "Write a C program that forks and reaps children",
            "Kill a zombie's parent to orphan-adopt it",
        ],
        "markdown": """\
## Overview

A **zombie process** is a child that has exited but whose exit status has not
yet been collected by its parent. It holds no resources — just a PID and an
entry in the process table — but a flood of zombies can exhaust PID space.

## How Zombies Are Created

```
Parent forks → child runs → child exits → parent never calls wait()
                                           ↓
                                     ZOMBIE (state Z)
```

The kernel keeps the child's exit status around until the parent reads it via
`wait()` or `waitpid()`. Without that call, the child becomes a zombie.

## Identifying Zombies

```bash
# Look for state 'Z' in ps output
ps aux | awk '$8 == "Z"'

# Or with ps forest to see the parent relationship
ps auxf | grep -A2 'Z'

# Check /proc directly
cat /proc/<pid>/status | grep State
```

## Proper Child Reaping in C

```c
#include <sys/wait.h>
#include <unistd.h>
#include <stdio.h>

int main(void) {
    pid_t pid = fork();

    if (pid == 0) {
        // Child: do some work then exit
        _exit(0);
    }

    // Parent: reap the child
    int status;
    waitpid(pid, &status, 0);

    if (WIFEXITED(status))
        printf("Child exited with code %d\\n", WEXITSTATUS(status));

    return 0;
}
```

For long-running daemons that fork many children, use `SIGCHLD`:

```c
signal(SIGCHLD, SIG_IGN);   // auto-reap on Linux (non-POSIX shortcut)
// or install a handler that loops waitpid(-1, NULL, WNOHANG)
```

## Killing Zombies by Targeting the Parent

```bash
# Find zombie's parent PID
ps -o ppid= -p <zombie_pid>

# Send SIGTERM to the parent to trigger reaping or orphan adoption
kill -TERM <parent_pid>
# init (PID 1) will then adopt and reap the zombie
```

## Tips & Gotchas

- Zombies **cannot be killed directly** — they're already dead. Target the parent.
- A well-written daemon uses `SA_NOCLDWAIT` in `sigaction` or double-forks to avoid zombie accumulation.
- `systemd` and other init systems automatically reap adopted orphans.
""",
    },
    {
        "id": "CH-06",
        "title": "CRON_SCHEDULING",
        "tags": ["CRONTAB", "ANACRON"],
        "difficulty": "BEGINNER [#--]",
        "category": "AUTOMATION",
        "description": (
            "Schedule jobs like a clock-maker. Learn cron syntax, user vs "
            "system crontabs, and anacron for machines that don't run 24/7."
        ),
        "objectives": [
            "Schedule a daily backup at 02:00",
            "Run a script every 5 minutes",
            "Configure anacron for a laptop",
        ],
        "markdown": """\
## Overview

`cron` is the Unix job scheduler. It wakes up every minute, reads **crontab**
files, and runs any commands whose time expression matches the current time.

## Crontab Syntax

```
┌──────── minute        (0-59)
│ ┌────── hour          (0-23)
│ │ ┌──── day of month  (1-31)
│ │ │ ┌── month         (1-12)
│ │ │ │ ┌ day of week   (0-7, 0 and 7 = Sunday)
│ │ │ │ │
* * * * *  command_to_run
```

### Common Examples

```cron
# Daily backup at 02:00
0 2 * * *  /usr/local/bin/backup.sh

# Every 5 minutes
*/5 * * * *  /opt/monitor/check.sh

# Weekdays at 08:30
30 8 * * 1-5  /usr/bin/send_report.py

# First day of every month
0 0 1 * *  /usr/local/bin/monthly_cleanup.sh
```

## Managing Crontabs

```bash
crontab -e          # edit YOUR crontab (opens $EDITOR)
crontab -l          # list your current jobs
crontab -r          # remove ALL your jobs (careful!)
crontab -u alice -e # edit another user's crontab (as root)
```

System-wide crontabs live in `/etc/cron.d/`, `/etc/cron.daily/`, etc.

## anacron — For Machines That Aren't Always On

`anacron` runs jobs that were missed while the machine was off (laptops, VMs).
It uses **day-granularity** rather than minute-granularity.

```
# /etc/anacrontab format:
# period  delay  job-id    command
  1       5      daily-backup  /usr/local/bin/backup.sh
  7       10     weekly-report /usr/local/bin/report.sh
```

- **period**: how many days between runs
- **delay**: minutes to wait after boot before starting

## Tips & Gotchas

- Cron runs with a **minimal environment** — always use full paths to binaries.
- Redirect output to avoid cron emailing you: `command >> /var/log/myjob.log 2>&1`
- Use `MAILTO=""` at the top of a crontab to silence all emails.
- Test your script manually as the cron user before scheduling it.
""",
    },
    {
        "id": "CH-07",
        "title": "SYSTEMD_UNITS",
        "tags": ["SERVICES", "TARGETS"],
        "difficulty": "ADVANCED [###]",
        "category": "INIT_SYSTEM",
        "description": (
            "Tame systemd. Write unit files, define dependencies, set up "
            "socket activation, and understand targets as the modern "
            "replacement for runlevels."
        ),
        "objectives": [
            "Write a .service unit for a Python app",
            "Define a Before= dependency between units",
            "Enable a unit to start on multi-user.target",
        ],
        "markdown": """\
## Overview

`systemd` is the init system on most modern Linux distributions. It manages
**units** — declarative configuration files that describe services, sockets,
mount points, timers, and more.

## Anatomy of a .service Unit

```ini
# /etc/systemd/system/myapp.service
[Unit]
Description=My Python Application
Documentation=https://example.com/docs
After=network.target           # start after network is up
Requires=postgresql.service    # hard dependency

[Service]
Type=simple
User=myapp
WorkingDirectory=/opt/myapp
ExecStart=/usr/bin/python3 /opt/myapp/main.py
ExecReload=/bin/kill -HUP $MAINPID
Restart=on-failure
RestartSec=5s
Environment=APP_ENV=production

[Install]
WantedBy=multi-user.target    # enable for normal multi-user boot
```

## Key Dependency Directives

| Directive | Meaning |
|-----------|---------|
| `After=` | Start this unit *after* the listed unit(s) |
| `Before=` | Start this unit *before* the listed unit(s) |
| `Requires=` | Hard dependency — if it fails, this fails too |
| `Wants=` | Soft dependency — failure is tolerated |
| `BindsTo=` | If the dependency stops, stop this unit too |

## Managing Units

```bash
# Reload unit files after editing
systemctl daemon-reload

# Enable (auto-start at boot) and start immediately
systemctl enable --now myapp.service

# Status, logs, restart
systemctl status myapp.service
journalctl -u myapp.service -f    # follow logs
systemctl restart myapp.service

# Check what would start at a given target
systemctl list-dependencies multi-user.target
```

## Targets (Modern Runlevels)

| Target | Equivalent Runlevel | Purpose |
|--------|--------------------:|---------|
| `rescue.target` | 1 | Single-user, minimal |
| `multi-user.target` | 3 | Network up, no GUI |
| `graphical.target` | 5 | Full desktop |

```bash
# Switch target temporarily
systemctl isolate rescue.target

# Set default boot target
systemctl set-default multi-user.target
```

## Tips & Gotchas

- Always run `systemctl daemon-reload` after editing a unit file — systemd caches them.
- Use `Type=notify` (with `sd_notify`) for apps that take time to initialize; systemd will wait for the ready signal.
- `journalctl -b -u myapp` shows logs from the current boot only — useful after a crash.
- `systemd-analyze blame` reveals which units are slowing down boot time.
""",
    },
     {
        "id": "CH-08",
        "title": "SSH_HARDENING",
        "tags": ["SSHD", "PUBKEY", "PORT_KNOCKING"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "SECURITY",
        "description": "Harden an OpenSSH server against brute-force and unauthorized access. Configure key-based authentication, disable dangerous defaults, and layer on port knocking for stealth.",
        "objectives": [
            "Disable root login and password authentication in sshd_config",
            "Generate and deploy an Ed25519 key pair",
            "Set up port knocking with knockd"
        ],
        "markdown": "## Overview\n\nSSH is the front door of every Linux server. A misconfigured `sshd` is responsible for a huge proportion of real-world compromises. Hardening it is one of the highest-ROI security tasks you can perform.\n\n## Key sshd_config Directives\n\n```bash\n# /etc/ssh/sshd_config — critical settings\nPort 2222                        # move off default port (security by obscurity, but reduces noise)\nPermitRootLogin no               # never allow direct root SSH\nPasswordAuthentication no        # keys only\nPubkeyAuthentication yes\nAuthorizationKeysFile .ssh/authorized_keys\nX11Forwarding no                 # disable unless needed\nAllowTcpForwarding no\nMaxAuthTries 3\nLoginGraceTime 20\nAllowUsers deploy alice          # whitelist specific users\nClientAliveInterval 300\nClientAliveCountMax 2\n```\n\nAfter editing, always validate before reloading:\n\n```bash\nsshd -t                          # test config syntax\nsystemctl reload sshd\n```\n\n## Generating and Deploying Ed25519 Keys\n\nEd25519 keys are smaller, faster, and more secure than RSA-2048.\n\n```bash\n# On your local machine\nssh-keygen -t ed25519 -C \"alice@workstation\" -f ~/.ssh/id_ed25519\n\n# Copy the public key to the server\nssh-copy-id -i ~/.ssh/id_ed25519.pub alice@server\n\n# Manual equivalent\ncat ~/.ssh/id_ed25519.pub | ssh alice@server \\\n  'mkdir -p ~/.ssh && chmod 700 ~/.ssh && \\\n   cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys'\n```\n\n## Restricting Keys in authorized_keys\n\nYou can constrain what a specific key is allowed to do:\n\n```bash\n# /home/deploy/.ssh/authorized_keys\ncommand=\"/usr/local/bin/deploy.sh\",no-pty,no-agent-forwarding,no-x11-forwarding ssh-ed25519 AAAA...\n```\n\nThis key can only run `deploy.sh` — nothing else.\n\n## Port Knocking with knockd\n\n```bash\napt install knockd\n\n# /etc/knockd.conf\n[options]\n    UseSyslog\n    Interface = eth0\n\n[openSSH]\n    sequence    = 7000,8000,9000\n    seq_timeout = 5\n    command     = /sbin/iptables -A INPUT -s %IP% -p tcp --dport 2222 -j ACCEPT\n    tcpflags    = syn\n\n[closeSSH]\n    sequence    = 9000,8000,7000\n    seq_timeout = 5\n    command     = /sbin/iptables -D INPUT -s %IP% -p tcp --dport 2222 -j ACCEPT\n    tcpflags    = syn\n```\n\nTo knock from a client:\n\n```bash\nknock -v server 7000 8000 9000\nssh -p 2222 alice@server\n```\n\n## Tips & Gotchas\n\n- Keep a second SSH session open while testing config changes — if you lock yourself out, you still have a lifeline.\n- `fail2ban` complements key-only auth by banning IPs that probe for valid usernames.\n- Use `ssh -vvv` on the client to diagnose auth failures in detail.\n- `AllowUsers` takes precedence over everything else — forgetting to add a user here is a common lockout cause.\n"
    },
    {
        "id": "CH-09",
        "title": "LVM_MANAGEMENT",
        "tags": ["PV", "VG", "LV", "RESIZE"],
        "difficulty": "ADVANCED [###]",
        "category": "FILESYSTEM",
        "description": "Take control of storage with the Logical Volume Manager. Create physical volumes, volume groups, and logical volumes. Resize volumes online and snapshot filesystems for zero-downtime backups.",
        "objectives": [
            "Create a volume group from two physical disks",
            "Extend a logical volume and resize its ext4 filesystem online",
            "Take an LVM snapshot and mount it read-only"
        ],
        "markdown": "## Overview\n\nLVM adds a virtualization layer between physical disks and filesystems. It lets you resize, snapshot, and migrate storage without downtime — things the fixed partition table cannot do.\n\n## The Three-Layer Model\n\n```\nPhysical Volumes (PV)  →  /dev/sdb, /dev/sdc\n        ↓\nVolume Group (VG)      →  vg_data   (pool of all PV space)\n        ↓\nLogical Volumes (LV)   →  /dev/vg_data/lv_home, /dev/vg_data/lv_www\n        ↓\nFilesystems            →  ext4, xfs, btrfs on top of each LV\n```\n\n## Creating the Stack\n\n```bash\n# 1. Initialize physical volumes\npvcreate /dev/sdb /dev/sdc\npvs                            # verify\n\n# 2. Create a volume group\nvgcreate vg_data /dev/sdb /dev/sdc\nvgs\n\n# 3. Create logical volumes\nlvcreate -L 20G  -n lv_www  vg_data    # fixed size\nlvcreate -l 100%FREE -n lv_data vg_data # use all remaining space\nlvs\n\n# 4. Make filesystems\nmkfs.ext4 /dev/vg_data/lv_www\nmkfs.xfs  /dev/vg_data/lv_data\n\n# 5. Mount\nmount /dev/vg_data/lv_www /var/www\n```\n\n## Extending a Volume Online\n\next4 and xfs both support online resize (no unmount needed).\n\n```bash\n# Add 10G to the logical volume\nlvextend -L +10G /dev/vg_data/lv_www\n\n# Grow the filesystem to fill the new space\nresize2fs /dev/vg_data/lv_www          # ext4\n# xfs_growfs /var/www                 # xfs (use mountpoint)\n\n# Combined shortcut for ext4\nlvextend -r -L +10G /dev/vg_data/lv_www   # -r calls resize2fs automatically\n```\n\n## LVM Snapshots\n\nSnapshots freeze a point-in-time view of an LV using copy-on-write.\n\n```bash\n# Create a 2G snapshot of lv_www\nlvcreate -L 2G -s -n lv_www_snap /dev/vg_data/lv_www\n\n# Mount it read-only for backup\nmount -o ro /dev/vg_data/lv_www_snap /mnt/snapshot\ntarsnapshot /mnt/snapshot /backup/www_$(date +%F).tar.gz\n\n# Remove snapshot when done\numount /mnt/snapshot\nlvremove /dev/vg_data/lv_www_snap\n```\n\n> The snapshot volume must be large enough to hold all writes to the origin during the backup window. If it fills up, the snapshot becomes invalid.\n\n## Tips & Gotchas\n\n- `vgextend vg_data /dev/sdd` adds a new disk to an existing group without downtime.\n- `pvmove /dev/sdb` migrates all extents off a disk — use before decommissioning hardware.\n- Thin provisioning (`lvcreate --thin`) over-commits space; monitor with `lvs -a` to catch thin pools nearing capacity.\n- Always add LVM volumes to `/etc/fstab` using the stable `/dev/vg_name/lv_name` path, not `/dev/sdX`.\n"
    },
    {
        "id": "CH-10",
        "title": "BASH_SCRIPTING",
        "tags": ["ARRAYS", "GETOPTS", "TRAPS", "HEREDOC"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "AUTOMATION",
        "description": "Write production-quality bash scripts. Go beyond one-liners: handle options with getopts, use arrays for safe argument passing, write reusable functions, and make scripts fail safely with proper error handling.",
        "objectives": [
            "Write a script that accepts flags with getopts",
            "Use an array to safely pass filenames with spaces to a command",
            "Implement a cleanup trap that fires on EXIT, SIGINT, and SIGTERM"
        ],
        "markdown": "## Overview\n\nBash is everywhere, but most bash scripts in the wild are fragile. This challenge focuses on the patterns that separate a throwaway one-liner from a script you'd commit to production.\n\n## Failing Safely — Set Options\n\nAlways start non-trivial scripts with:\n\n```bash\n#!/usr/bin/env bash\nset -euo pipefail\nIFS=$'\\n\\t'\n```\n\n| Option | Effect |\n|--------|--------|\n| `-e` | Exit immediately on error |\n| `-u` | Treat unset variables as errors |\n| `-o pipefail` | Propagate pipe failures (not just last command) |\n| `IFS=$'\\n\\t'` | Prevent word-splitting on spaces |\n\n## Parsing Options with getopts\n\n```bash\nusage() { echo \"Usage: $0 [-v] [-o output] input...\"; exit 1; }\n\nVERBOSE=0\nOUTPUT=\"/tmp/out\"\n\nwhile getopts \":vo:\" opt; do\n    case $opt in\n        v) VERBOSE=1 ;;\n        o) OUTPUT=\"$OPTARG\" ;;\n        :) echo \"Option -$OPTARG requires an argument\"; usage ;;\n        ?) echo \"Unknown option: -$OPTARG\"; usage ;;\n    esac\ndone\n\nshift $((OPTIND - 1))    # remaining args are now in $@\n```\n\n## Arrays for Safe Argument Handling\n\n```bash\n# Building a command safely — handles filenames with spaces\nfiles=()\nwhile IFS= read -r -d '' f; do\n    files+=(\"$f\")\ndone < <(find /data -name '*.log' -print0)\n\n# Pass the array — NEVER do: cmd ${files[@]} (splits on spaces)\ncmd \"${files[@]}\"\n\n# Indexed access\necho \"First file: ${files[0]}\"\necho \"Count: ${#files[@]}\"\n```\n\n## Cleanup Traps\n\n```bash\nTMPDIR=$(mktemp -d)\nLOCKFILE=\"/var/run/myscript.lock\"\n\ncleanup() {\n    local exit_code=$?\n    rm -rf \"$TMPDIR\"\n    rm -f \"$LOCKFILE\"\n    [[ $exit_code -ne 0 ]] && echo \"Script failed with exit $exit_code\" >&2\n    exit $exit_code\n}\n\ntrap cleanup EXIT          # fires on any exit, including errors\ntrap 'cleanup; exit 130' SIGINT\ntrap 'cleanup; exit 143' SIGTERM\n```\n\n## Reusable Functions and Logging\n\n```bash\n# Consistent logging with timestamps\nlog()  { printf '[%s] INFO  %s\\n' \"$(date +%T)\" \"$*\"; }\nwarn() { printf '[%s] WARN  %s\\n' \"$(date +%T)\" \"$*\" >&2; }\ndie()  { printf '[%s] ERROR %s\\n' \"$(date +%T)\" \"$*\" >&2; exit 1; }\n\n# Here-document for multi-line output\ncat <<'EOF'\nThis text is printed verbatim.\nNo $variable expansion happens inside single-quoted EOF.\nEOF\n\n# Indented heredoc (bash 4+ with <<-)\ncat <<-EOF\n    This strips leading tabs (not spaces).\nEOF\n```\n\n## Tips & Gotchas\n\n- `[[ ]]` is safer than `[ ]` — supports `&&`, `||`, regex matching, and no word-splitting surprises.\n- Quote everything: `\"$variable\"` not `$variable`.\n- `local` variables in functions prevent contaminating global scope.\n- `shellcheck` is a static analyzer for bash — run it on every script before committing.\n"
    },
    {
        "id": "CH-11",
        "title": "DISK_FORENSICS",
        "tags": ["DD", "FSCK", "DEBUGFS", "INODE"],
        "difficulty": "ADVANCED [###]",
        "category": "FILESYSTEM",
        "description": "Recover deleted files, inspect raw inodes, and repair corrupt filesystems. Use dd for disk imaging, debugfs to poke at ext4 internals, and fsck to bring a damaged filesystem back from the dead.",
        "objectives": [
            "Create a bit-perfect disk image with dd and verify its hash",
            "Recover a recently deleted file using debugfs",
            "Repair a corrupt ext4 filesystem with fsck"
        ],
        "markdown": "## Overview\n\nWhen storage goes wrong — corruption, accidental deletion, ransomware — you need low-level tools that operate below the filesystem abstraction. This challenge builds the skills to image, inspect, and recover.\n\n## Disk Imaging with dd\n\n```bash\n# Image an entire disk to a file\ndd if=/dev/sdb of=/backup/sdb.img bs=4M status=progress conv=sync,noerror\n\n# Verify integrity with checksums\nsha256sum /dev/sdb > /backup/sdb.sha256\nsha256sum /backup/sdb.img   # should match\n\n# Compress on the fly\ndd if=/dev/sdb bs=4M status=progress | gzip -c > /backup/sdb.img.gz\n\n# Restore an image back to a disk\ndd if=/backup/sdb.img of=/dev/sdb bs=4M status=progress\n```\n\n> Always work on an image, never the live disk — forensics principle #1.\n\n## Understanding Inodes\n\nEvery file is an inode. The filename is just a directory entry pointing to one.\n\n```bash\n# Find a file's inode number\nls -i /etc/passwd\nstat /etc/passwd\n\n# Find all hard links to an inode\nfind / -inum 123456 2>/dev/null\n\n# When a file is \"deleted\", its directory entry is removed but the inode\n# remains until all links reach zero AND no process has it open.\nlsof /path/to/deleted/file   # check if still open\n```\n\n## File Recovery with debugfs\n\n`debugfs` gives you direct access to ext2/3/4 filesystem internals.\n\n```bash\n# Open filesystem read-only (ALWAYS do this on originals)\ndebugfs -R 'lsdel' /dev/sdb1    # list recently deleted inodes\n\n# Interactive session\ndebugfs /dev/sdb1\n  > lsdel                        # list deleted inodes\n  > stat <inode_number>          # inspect an inode\n  > dump <inode_number> /tmp/recovered_file   # extract file data\n  > quit\n\n# One-liner recovery\ndebugfs -R \"dump <123456> /tmp/recovered\" /dev/sdb1\n```\n\nFor NTFS or FAT, use `testdisk` and `photorec` instead.\n\n## Filesystem Repair with fsck\n\n```bash\n# NEVER run fsck on a mounted filesystem\numount /dev/sdb1\n\n# Check without making changes\nfsck -n /dev/sdb1\n\n# Repair automatically (answers 'yes' to all prompts)\nfsck -y /dev/sdb1\n\n# Force check even if filesystem appears clean\nfsck -f /dev/sdb1\n\n# For specific filesystem types\nfsck.ext4 -v /dev/sdb1\nxfs_repair /dev/sdc1    # XFS equivalent\n```\n\n## Reading Raw Blocks\n\n```bash\n# Read the superblock\nmke2fs -n /dev/sdb1        # simulate: shows where superblock backups are\ndebugfs -R 'show_super_stats' /dev/sdb1\n\n# Restore from backup superblock if primary is corrupt\ne2fsck -b 8193 /dev/sdb1   # 8193 is a common backup superblock location\n```\n\n## Tips & Gotchas\n\n- Time is critical after deletion — every write to the disk risks overwriting the inode data. Unmount immediately.\n- `conv=noerror` in dd skips unreadable sectors rather than aborting — critical for failing drives.\n- `badblocks -v /dev/sdb` maps bad sectors; pass the output to `fsck -l` to exclude them permanently.\n- `tune2fs -l /dev/sdb1` shows ext4 filesystem metadata including last mount time and error count.\n"
    },
    {
        "id": "CH-12",
        "title": "CONTAINER_INTERNALS",
        "tags": ["NAMESPACES", "CGROUPS", "SECCOMP"],
        "difficulty": "ADVANCED [###]",
        "category": "VIRTUALIZATION",
        "description": "Pull back the curtain on containers. Build a minimal container from scratch using Linux namespaces and cgroups — no Docker required. Understand what container runtimes actually do under the hood.",
        "objectives": [
            "Create an isolated process using unshare with UTS, PID, and mount namespaces",
            "Limit a process group to 256MB RAM using cgroups v2",
            "Apply a seccomp profile to restrict syscalls"
        ],
        "markdown": "## Overview\n\nContainers are not magic — they are processes with restricted views of the system. The kernel provides two key mechanisms: **namespaces** (what the process *sees*) and **cgroups** (what it *can use*). Together they create the illusion of isolation.\n\n## Linux Namespaces\n\n| Namespace | Flag | Isolates |\n|-----------|------|----------|\n| UTS | `CLONE_NEWUTS` | Hostname and domain name |\n| PID | `CLONE_NEWPID` | Process ID tree |\n| Mount | `CLONE_NEWNS` | Filesystem mounts |\n| Network | `CLONE_NEWNET` | Network interfaces, routes |\n| User | `CLONE_NEWUSER` | UID/GID mappings |\n| IPC | `CLONE_NEWIPC` | System V IPC, POSIX MQs |\n\n## Building a Container with unshare\n\n```bash\n# Create a root filesystem\nmkdir -p /tmp/mycontainer\ndebootstrap --variant=minbase focal /tmp/mycontainer\n\n# Launch an isolated shell\nunshare \\\n  --uts \\\n  --pid \\\n  --mount \\\n  --fork \\\n  --mount-proc=/tmp/mycontainer/proc \\\n  chroot /tmp/mycontainer /bin/bash\n\n# Inside the container — it sees a fresh process tree\nps aux            # only sees its own processes\nhostname          # can set without affecting host\nhostname mybox\n```\n\n## Cgroups v2 — Resource Limits\n\n```bash\n# Check if cgroupv2 is active\ncat /proc/filesystems | grep cgroup\nmount | grep cgroup2\n\n# Create a new cgroup\nmkdir /sys/fs/cgroup/myapp\n\n# Set a 256MB memory limit\necho $((256 * 1024 * 1024)) > /sys/fs/cgroup/myapp/memory.max\n\n# Limit to 50% of one CPU\necho '50000 100000' > /sys/fs/cgroup/myapp/cpu.max\n\n# Add a process to the cgroup\necho <PID> > /sys/fs/cgroup/myapp/cgroup.procs\n\n# Monitor usage\ncat /sys/fs/cgroup/myapp/memory.current\ncat /sys/fs/cgroup/myapp/cpu.stat\n```\n\n## seccomp — Syscall Filtering\n\n```bash\n# Run a process with a restricted syscall whitelist using Docker's seccomp\n# Manually, use libseccomp or the seccomp BPF interface\n\n# See what syscalls a process makes\nstrace -c -f ls /tmp 2>&1 | tail -20\n\n# Apply a seccomp profile with unshare + systemd-run\nsystemd-run --scope \\\n  -p \"SystemCallFilter=~@clock @debug @module @mount @raw-io\" \\\n  /bin/bash\n\n# Generate a profile from strace output (using oci-seccomp-bpf-hook)\nstrace -f -e trace=all -o /tmp/strace.out ./myapp\n```\n\n## Overlay Filesystems (Union Mounts)\n\nDocker layers are implemented with `overlayfs`:\n\n```bash\nmkdir -p /tmp/overlay/{lower,upper,work,merged}\necho 'base file' > /tmp/overlay/lower/base.txt\n\nmount -t overlay overlay \\\n  -o lowerdir=/tmp/overlay/lower,\\\n     upperdir=/tmp/overlay/upper,\\\n     workdir=/tmp/overlay/work \\\n  /tmp/overlay/merged\n\n# Writes go to 'upper', reads fall through to 'lower'\necho 'new file' > /tmp/overlay/merged/new.txt\nls /tmp/overlay/upper     # only new.txt here — lower is untouched\n```\n\n## Tips & Gotchas\n\n- User namespaces allow unprivileged users to create containers but require careful UID mapping.\n- `nsenter -t <PID> --all` joins all namespaces of a running container — useful for debugging.\n- cgroups v1 and v2 coexist on many systems; Docker may use v1 even if v2 is available.\n- `runc` is the reference OCI container runtime — reading its source is the best way to understand the full picture.\n"
    },
    {
        "id": "CH-13",
        "title": "LOG_AGGREGATION",
        "tags": ["RSYSLOG", "JOURNALD", "LOGROTATE"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "OBSERVABILITY",
        "description": "Build a centralized logging pipeline. Configure rsyslog to forward logs over TCP, query and filter journald with journalctl, and set up logrotate to prevent disks from filling up.",
        "objectives": [
            "Configure rsyslog to forward auth logs to a remote syslog server",
            "Query journald for all critical kernel messages since last boot",
            "Write a logrotate config for a high-volume application log"
        ],
        "markdown": "## Overview\n\nLogs are your audit trail, your debugging lifeline, and your security forensics source. A proper logging setup centralizes them before a compromise can erase them, and rotates them before they fill the disk.\n\n## rsyslog — Forwarding Logs\n\nrsyslog uses a **facility.severity** filter syntax.\n\n```bash\n# /etc/rsyslog.d/50-forward-auth.conf\n\n# Load TCP output module\nmodule(load=\"omfwd\")\n\n# Forward auth facility to remote server over TCP\nif $syslogfacility-text == 'auth' then {\n    action(\n        type=\"omfwd\"\n        target=\"192.168.1.100\"\n        port=\"514\"\n        protocol=\"tcp\"\n        action.resumeRetryCount=\"100\"\n        queue.type=\"linkedList\"\n        queue.size=\"10000\"\n    )\n}\n\n# On the receiving server — listen on TCP 514\nmodule(load=\"imtcp\")\ninput(type=\"imtcp\" port=\"514\")\n$template RemoteLogs,\"/var/log/remote/%HOSTNAME%/%PROGRAMNAME%.log\"\n*.* ?RemoteLogs\n```\n\n```bash\nsystemctl restart rsyslog\n# Test with logger\nlogger -p auth.warning \"Test auth message\"\n```\n\n## journald — Querying Structured Logs\n\n```bash\n# All logs from current boot\njournalctl -b\n\n# Previous boot (useful post-crash)\njournalctl -b -1\n\n# Kernel messages only, priority err and above\njournalctl -k -p err\n\n# Since last boot, from a specific unit\njournalctl -b -u nginx.service\n\n# Time-bounded query\njournalctl --since \"2024-01-15 08:00\" --until \"2024-01-15 12:00\"\n\n# Follow live (like tail -f)\njournalctl -f -u myapp.service\n\n# Export to JSON for processing\njournalctl -b -u myapp -o json | jq '.MESSAGE'\n\n# Disk usage\njournalctl --disk-usage\n\n# Vacuum old journals\njournalctl --vacuum-size=500M\njournalctl --vacuum-time=30d\n```\n\n## journald Persistent Storage\n\nBy default journald logs to RAM (`/run/log/journal`). To persist across reboots:\n\n```bash\n# /etc/systemd/journald.conf\n[Journal]\nStorage=persistent          # writes to /var/log/journal\nSystemMaxUse=2G             # cap total disk usage\nSystemKeepFree=500M         # always leave this much free\nMaxRetentionSec=1month\nCompress=yes\n```\n\n## logrotate\n\n```bash\n# /etc/logrotate.d/myapp\n/var/log/myapp/*.log {\n    daily                    # rotate daily\n    rotate 30                # keep 30 rotated files\n    compress                 # gzip old logs\n    delaycompress            # don't compress the most recent rotation\n    missingok                # don't error if log file is missing\n    notifempty               # don't rotate empty files\n    create 640 myapp adm    # create new log with these perms\n    postrotate\n        systemctl kill -s HUP myapp.service  # tell app to reopen log files\n    endscript\n}\n```\n\n```bash\n# Test without executing\nlogrotate -d /etc/logrotate.d/myapp\n\n# Force rotation now\nlogrotate -f /etc/logrotate.d/myapp\n```\n\n## Tips & Gotchas\n\n- Send logs over TCP not UDP for reliability; add TLS with `StreamDriver=gtls` in rsyslog.\n- `journalctl -o verbose` shows all metadata fields — useful for building precise filters.\n- Applications that write directly to files (not syslog) need `postrotate` scripts to reopen file handles, or they'll keep writing to the old inode.\n- `logger` is the easiest way to inject test messages into syslog from any script.\n"
    },
    {
        "id": "CH-14",
        "title": "KERNEL_TUNING",
        "tags": ["SYSCTL", "PROC", "HUGEPAGES"],
        "difficulty": "ADVANCED [###]",
        "category": "PERFORMANCE",
        "description": "Squeeze performance and security out of the Linux kernel via sysctl. Tune the network stack for high-throughput workloads, harden the kernel against common attacks, and configure HugePages for memory-intensive applications.",
        "objectives": [
            "Increase the maximum number of open file descriptors system-wide",
            "Tune TCP buffers for a 10Gbps network link",
            "Harden the kernel against ICMP attacks and IP spoofing"
        ],
        "markdown": "## Overview\n\n`sysctl` exposes a live interface to kernel parameters through the `/proc/sys/` virtual filesystem. Changes take effect immediately and can be made permanent via `/etc/sysctl.d/`. The right tuning can double throughput on a network-bound workload.\n\n## Reading and Setting Parameters\n\n```bash\n# Read a parameter\nsysctl net.core.rmem_max\ncat /proc/sys/net/core/rmem_max    # equivalent\n\n# Set temporarily (lost on reboot)\nsysctl -w net.core.rmem_max=134217728\n\n# Set permanently\necho 'net.core.rmem_max = 134217728' > /etc/sysctl.d/99-tuning.conf\nsysctl --system    # reload all .conf files\n\n# List all parameters\nsysctl -a | grep tcp\n```\n\n## File Descriptor Limits\n\n```bash\n# /etc/sysctl.d/99-fdlimits.conf\nfs.file-max = 2097152          # system-wide FD limit\n\n# Per-user limits in /etc/security/limits.conf\n# (requires pam_limits — active on most distros)\n*    soft  nofile  65536\n*    hard  nofile  131072\nroot soft  nofile  65536\n\n# Check current limits for a running process\ncat /proc/<PID>/limits | grep 'open files'\n\n# Check system-wide usage\ncat /proc/sys/fs/file-nr   # [used, unused, max]\n```\n\n## Network Stack Tuning for High Throughput\n\n```bash\n# /etc/sysctl.d/99-network.conf\n\n# Increase TCP buffer sizes (for 10GbE with 1ms RTT, ~10MB is right)\nnet.core.rmem_max          = 134217728\nnet.core.wmem_max          = 134217728\nnet.ipv4.tcp_rmem          = 4096 87380 134217728\nnet.ipv4.tcp_wmem          = 4096 65536 134217728\n\n# Backlog for new connections\nnet.core.somaxconn         = 65535\nnet.core.netdev_max_backlog = 250000\n\n# Enable BBR congestion control (Linux 4.9+)\nnet.core.default_qdisc     = fq\nnet.ipv4.tcp_congestion_control = bbr\n\n# Reuse TIME_WAIT sockets faster\nnet.ipv4.tcp_tw_reuse      = 1\nnet.ipv4.tcp_fin_timeout   = 15\n```\n\n## Kernel Hardening\n\n```bash\n# /etc/sysctl.d/99-hardening.conf\n\n# Block ICMP redirects (common MITM vector)\nnet.ipv4.conf.all.accept_redirects  = 0\nnet.ipv6.conf.all.accept_redirects  = 0\n\n# IP spoofing protection (reverse path filter)\nnet.ipv4.conf.all.rp_filter         = 1\nnet.ipv4.conf.default.rp_filter     = 1\n\n# Ignore ICMP broadcast requests\nnet.ipv4.icmp_echo_ignore_broadcasts = 1\n\n# Protect against SYN flood\nnet.ipv4.tcp_syncookies             = 1\nnet.ipv4.tcp_max_syn_backlog        = 2048\n\n# Disable IP source routing\nnet.ipv4.conf.all.accept_source_route = 0\n\n# Hide kernel pointers from unprivileged users\nkernel.kptr_restrict = 2\nkernel.dmesg_restrict = 1\n\n# Prevent core dumps from setuid programs\nfs.suid_dumpable = 0\n```\n\n## HugePages for Databases\n\nDatabases (PostgreSQL, Oracle, Redis) benefit enormously from 2MB HugePages instead of 4KB pages.\n\n```bash\n# Calculate how many 2MB pages you need (e.g., 16GB shared memory)\n# 16 * 1024 / 2 = 8192 pages\n\n# /etc/sysctl.d/99-hugepages.conf\nvm.nr_hugepages = 8192\nvm.hugetlb_shm_group = 1001    # GID of the postgres group\n\n# Verify\ngrep Huge /proc/meminfo\n\n# For PostgreSQL, also set:\n# huge_pages = on in postgresql.conf\n```\n\n## Tips & Gotchas\n\n- `sysctl -w net.ipv4.ip_forward=1` is required for routing/NAT — easy to forget.\n- Changes to `limits.conf` only apply to new login sessions; use `prlimit` to modify a running process.\n- `vm.swappiness=10` (not 0) is the standard advice for database servers — avoids OOM while reducing swap thrash.\n- `numactl --hardware` reveals NUMA topology; binding processes to a NUMA node can double memory throughput on multi-socket servers.\n"
    },
    {
        "id": "CH-15",
        "title": "TLS_CERTIFICATES",
        "tags": ["OPENSSL", "X509", "CFSSL", "LETS_ENCRYPT"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "SECURITY",
        "description": "Demystify TLS. Generate your own CA, issue signed certificates, inspect certificate chains, and automate renewal with Certbot. Understand the difference between DV, OV, and EV certs and what actually gets verified.",
        "objectives": [
            "Create a private CA and sign a server certificate with openssl",
            "Inspect a remote server's certificate chain with openssl s_client",
            "Set up automated Let's Encrypt certificate renewal with Certbot"
        ],
        "markdown": "## Overview\n\nTLS is the foundation of secure communication on the internet, yet most sysadmins treat certificate management as a black box. Understanding the PKI machinery lets you debug trust errors, run internal CAs, and automate renewal reliably.\n\n## The PKI Chain of Trust\n\n```\nRoot CA (self-signed, offline)  →  trusted by browsers/OS\n    ↓ signs\nIntermediate CA                 →  used for day-to-day issuance\n    ↓ signs\nLeaf certificate                →  presented by your server\n```\n\n## Creating a Private CA with openssl\n\n```bash\n# 1. Generate the root CA key and self-signed certificate (10-year validity)\nopenssl genrsa -aes256 -out ca.key 4096\nopenssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \\\n  -out ca.crt \\\n  -subj \"/C=US/O=Acme Corp/CN=Acme Root CA\"\n\n# 2. Generate the server key and CSR (Certificate Signing Request)\nopenssl genrsa -out server.key 2048\nopenssl req -new -key server.key -out server.csr \\\n  -subj \"/C=US/O=Acme Corp/CN=api.internal.example.com\"\n\n# 3. Create a v3 extension file for SANs (required by modern browsers)\ncat > v3.ext <<EOF\nauthorityKeyIdentifier=keyid,issuer\nbasicConstraints=CA:FALSE\nkeyUsage=digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\nsubjectAltName=@alt_names\n\n[alt_names]\nDNS.1 = api.internal.example.com\nDNS.2 = *.internal.example.com\nIP.1  = 192.168.1.50\nEOF\n\n# 4. Sign the CSR with the CA\nopenssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key \\\n  -CAcreateserial -out server.crt -days 365 \\\n  -sha256 -extfile v3.ext\n\n# 5. Verify\nopenssl verify -CAfile ca.crt server.crt\n```\n\n## Inspecting Certificates\n\n```bash\n# View a certificate's contents\nopenssl x509 -in server.crt -text -noout\n\n# Check expiry date specifically\nopenssl x509 -in server.crt -noout -dates\n\n# Inspect a remote server's chain\nopenssl s_client -connect example.com:443 -showcerts </dev/null 2>/dev/null \\\n  | openssl x509 -noout -text\n\n# Check if a key matches a certificate\nopenssl x509 -noout -modulus -in server.crt | md5sum\nopenssl rsa  -noout -modulus -in server.key | md5sum\n# Both hashes must match\n\n# Test TLS handshake and cipher negotiation\nopenssl s_client -connect example.com:443 -tls1_3\n```\n\n## Automated Let's Encrypt with Certbot\n\n```bash\n# Install\napt install certbot python3-certbot-nginx\n\n# Obtain and install a certificate (nginx plugin handles config)\ncertbot --nginx -d example.com -d www.example.com\n\n# Standalone mode (no web server running)\ncertbot certonly --standalone -d example.com\n\n# Wildcard cert (requires DNS challenge)\ncertbot certonly --manual --preferred-challenges dns \\\n  -d '*.example.com' -d example.com\n\n# Test auto-renewal\ncertbot renew --dry-run\n\n# Certbot installs a systemd timer; verify it:\nsystemctl status certbot.timer\n```\n\n## PEM, DER, PFX Format Conversions\n\n```bash\n# PEM → DER (binary)\nopenssl x509 -in cert.pem -outform DER -out cert.der\n\n# PEM → PFX (for IIS/Windows)\nopenssl pkcs12 -export -out cert.pfx \\\n  -inkey server.key -in server.crt -certfile ca.crt\n\n# PFX → PEM\nopenssl pkcs12 -in cert.pfx -nodes -out all.pem\n```\n\n## Tips & Gotchas\n\n- Missing SAN (Subject Alternative Name) causes Chrome/Firefox to reject certs with only a CN — always add SANs.\n- Distribute the CA cert to all clients that need to trust it: `/usr/local/share/ca-certificates/myca.crt` then `update-ca-certificates` on Debian.\n- `certbot renew` is idempotent and safe to run in cron daily — it only renews certs within 30 days of expiry.\n- Monitor expirations with `check_ssl_cert` (Nagios plugin) or Prometheus `ssl_exporter`.\n"
    },
    {
        "id": "CH-16",
        "title": "AWK_KUNG_FU",
        "tags": ["AWK", "PATTERNS", "BUILT_IN_VARS"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "DATA_STREAMS",
        "description": "Master awk — the pattern-action language of Unix text processing. Go beyond simple column printing to aggregation, multi-file processing, associative arrays, and formatted reports from raw log data.",
        "objectives": [
            "Sum the bytes transferred column in an nginx access log",
            "Print lines where a field exceeds a threshold",
            "Generate a frequency table of HTTP status codes from a log file"
        ],
        "markdown": "## Overview\n\n`awk` is a full programming language built around the idea of matching patterns and executing actions. It excels at structured text: logs, CSVs, tabular data. It is faster than Python for many one-pass problems and doesn't require a script file.\n\n## The Pattern-Action Model\n\n```bash\n# Syntax: awk '/pattern/ { action }' file\n\n# Print all lines (implicit action)\nawk '{ print }' file\n\n# Print only matching lines\nawk '/ERROR/' file\n\n# Print field 1 and 4 of lines matching a pattern\nawk '/404/ { print $1, $4 }' access.log\n\n# BEGIN and END blocks run once\nawk 'BEGIN { print \"START\" } /foo/ { count++ } END { print count }' file\n```\n\n## Built-in Variables\n\n| Variable | Meaning |\n|----------|---------|\n| `$0` | Entire current line |\n| `$1..$NF` | Fields 1 through NF |\n| `NF` | Number of fields in current line |\n| `NR` | Current record (line) number |\n| `FNR` | Record number within current file |\n| `FS` | Input field separator (default: whitespace) |\n| `OFS` | Output field separator (default: space) |\n| `RS` | Input record separator (default: newline) |\n\n## Practical Recipes\n\n```bash\n# Sum bytes transferred (field 10 in common log format)\nawk '{ bytes += $10 } END { printf \"Total: %.2f MB\\n\", bytes/1024/1024 }' access.log\n\n# Print lines where response time (field 7) exceeds 2 seconds\nawk '$7 > 2.0 { print NR\": \"$0 }' app.log\n\n# Frequency table of HTTP status codes\nawk '{ codes[$9]++ } END {\n    for (c in codes) printf \"%s\\t%d\\n\", c, codes[c]\n}' access.log | sort -k2 -rn\n\n# Print unique values of a column\nawk '!seen[$1]++' file\n\n# Change field separator to comma (CSV parsing)\nawk -F',' '{ print $1, $3 }' data.csv\n\n# Multi-file: print filename with each match\nawk 'FNR==1 { file=FILENAME } /ERROR/ { print file\": \"$0 }' *.log\n```\n\n## Associative Arrays\n\n```bash\n# Count requests per IP\nawk '{ ip_count[$1]++ }\nEND {\n    for (ip in ip_count)\n        if (ip_count[ip] > 1000)\n            print ip, ip_count[ip]\n}' access.log | sort -k2 -rn | head -20\n\n# Join two files on a key (file1 has id+name, file2 has id+score)\nawk 'NR==FNR { name[$1]=$2; next } $1 in name { print name[$1], $2 }' \\\n  names.txt scores.txt\n```\n\n## Formatted Reports\n\n```bash\nawk '\nBEGIN {\n    FS = \" \"\n    printf \"%-20s %10s %10s\\n\", \"URL\", \"Hits\", \"AvgTime\"\n    printf \"%-20s %10s %10s\\n\", \"---\", \"----\", \"-------\"\n}\n{\n    hits[$7]++\n    time[$7] += $NF\n}\nEND {\n    for (url in hits)\n        printf \"%-20s %10d %10.3f\\n\", url, hits[url], time[url]/hits[url]\n}' access.log | sort -k2 -rn | head -20\n```\n\n## Tips & Gotchas\n\n- `awk -F:` sets the field separator to colon — perfect for `/etc/passwd`.\n- String comparison vs numeric: `$3 > \"9\"` is lexicographic; `$3+0 > 9` forces numeric.\n- `gawk` (GNU awk) adds features like `PROCINFO`, `getline`, and true regex intervals.\n- For very large files, awk is typically faster than equivalent Python due to lower startup and GC overhead.\n"
    },
    {
        "id": "CH-17",
        "title": "ANSIBLE_PLAYBOOKS",
        "tags": ["IDEMPOTENCY", "ROLES", "VAULT"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "AUTOMATION",
        "description": "Automate infrastructure with Ansible. Write idempotent playbooks, structure them into reusable roles, manage secrets with Ansible Vault, and understand how Ansible's push model works under the hood.",
        "objectives": [
            "Write a playbook that installs and configures nginx idempotently",
            "Refactor the playbook into a role with defaults and handlers",
            "Encrypt a secrets file with Ansible Vault and reference it in a task"
        ],
        "markdown": "## Overview\n\nAnsible turns manual runbooks into reproducible, version-controlled automation. It uses SSH (no agent required) and a declarative YAML syntax. The key design principle is **idempotency** — running a playbook twice should produce the same result as running it once.\n\n## Inventory\n\n```ini\n# inventory/hosts.ini\n[webservers]\nweb1.example.com ansible_user=ubuntu\nweb2.example.com ansible_user=ubuntu\n\n[dbservers]\ndb1.example.com ansible_user=postgres ansible_port=2222\n\n[all:vars]\nansible_python_interpreter=/usr/bin/python3\n```\n\n## A Basic Playbook\n\n```yaml\n# site.yml\n---\n- name: Configure web servers\n  hosts: webservers\n  become: true               # sudo\n  vars:\n    nginx_port: 80\n    site_root: /var/www/html\n\n  tasks:\n    - name: Install nginx\n      apt:\n        name: nginx\n        state: present\n        update_cache: true\n      notify: Restart nginx   # fires handler only if this task changed\n\n    - name: Deploy site config\n      template:\n        src: nginx.conf.j2\n        dest: /etc/nginx/nginx.conf\n        owner: root\n        mode: '0644'\n      notify: Restart nginx\n\n    - name: Ensure nginx is running and enabled\n      service:\n        name: nginx\n        state: started\n        enabled: true\n\n  handlers:\n    - name: Restart nginx\n      service:\n        name: nginx\n        state: restarted\n```\n\n```bash\n# Run the playbook\nansible-playbook -i inventory/hosts.ini site.yml\n\n# Dry run (check mode)\nansible-playbook -i inventory/hosts.ini site.yml --check --diff\n\n# Limit to one host\nansible-playbook -i inventory/hosts.ini site.yml --limit web1.example.com\n\n# Run specific tags only\nansible-playbook site.yml --tags install\n```\n\n## Role Structure\n\n```\nroles/nginx/\n├── defaults/\n│   └── main.yml       # lowest-priority variables (easily overridden)\n├── vars/\n│   └── main.yml       # higher-priority variables\n├── tasks/\n│   └── main.yml       # the task list\n├── handlers/\n│   └── main.yml       # handlers\n├── templates/\n│   └── nginx.conf.j2  # Jinja2 templates\n├── files/\n│   └── index.html     # static files\n└── meta/\n    └── main.yml       # role dependencies\n```\n\n```yaml\n# roles/nginx/defaults/main.yml\nnginx_port: 80\nnginx_worker_processes: auto\nnginx_client_max_body_size: 10m\n\n# Use the role in a playbook\n- hosts: webservers\n  roles:\n    - role: nginx\n      vars:\n        nginx_port: 8080      # override default\n```\n\n## Ansible Vault for Secrets\n\n```bash\n# Encrypt a secrets file\nansible-vault encrypt secrets.yml\n\n# Edit it in-place\nansible-vault edit secrets.yml\n\n# Encrypt a single string value\nansible-vault encrypt_string 'my_db_password' --name 'db_password'\n\n# Reference in playbook\n- name: Create DB user\n  community.postgresql.postgresql_user:\n    name: myapp\n    password: \"{{ db_password }}\"\n\n# Run playbook with vault password file\nansible-playbook site.yml --vault-password-file ~/.vault_pass\n# Or interactively:\nansible-playbook site.yml --ask-vault-pass\n```\n\n## Tips & Gotchas\n\n- `changed_when: false` prevents a task from reporting changed even when it runs — use for read-only `command` tasks.\n- `block`/`rescue`/`always` provides try/catch/finally semantics in playbooks.\n- Ansible facts (`ansible_facts`) give you OS, IP, memory, and CPU info — available automatically via the `gather_facts` step.\n- Use `molecule` for role testing with Docker — test before you deploy.\n"
    },
    {
        "id": "CH-18",
        "title": "IPTABLES_FIREWALL",
        "tags": ["FILTER", "NAT", "CONNTRACK", "NFTABLES"],
        "difficulty": "ADVANCED [###]",
        "category": "NETWORKING",
        "description": "Build a stateful firewall from scratch with iptables. Design a default-deny policy, allow specific services, implement DNAT for port forwarding, and migrate the ruleset to modern nftables syntax.",
        "objectives": [
            "Implement a default-deny INPUT policy allowing only established, SSH, and HTTP/S",
            "Set up DNAT to forward port 80 on the WAN interface to an internal web server",
            "Translate the iptables ruleset to equivalent nftables rules"
        ],
        "markdown": "## Overview\n\nA firewall is your network perimeter. iptables is the classic Linux firewall using the Netfilter kernel framework. Understanding it deeply — chains, tables, connection tracking — prepares you both for legacy systems and for its modern successor nftables.\n\n## Packet Traversal Order\n\n```\nIncoming packet\n    → PREROUTING (nat) → [routing decision]\n          ↓ (destined for local process)\n        INPUT (filter)\n          ↓\n        Local process\n          ↓\n        OUTPUT (filter)\n          ↓ (or for forwarded packets)\n        FORWARD (filter)\n          ↓\n        POSTROUTING (nat)\n          ↓\nOutgoing packet\n```\n\n## Default-Deny Stateful Ruleset\n\n```bash\n#!/usr/bin/env bash\n# flush existing rules\niptables -F; iptables -X; iptables -t nat -F\n\n# Default policies\niptables -P INPUT   DROP\niptables -P FORWARD DROP\niptables -P OUTPUT  ACCEPT      # trust outbound\n\n# Loopback\niptables -A INPUT -i lo -j ACCEPT\n\n# Allow established/related connections (stateful)\niptables -A INPUT -m conntrack --ctstate ESTABLISHED,RELATED -j ACCEPT\n\n# SSH (rate-limited)\niptables -A INPUT -p tcp --dport 22 -m conntrack --ctstate NEW \\\n  -m limit --limit 5/min --limit-burst 10 -j ACCEPT\n\n# HTTP and HTTPS\niptables -A INPUT -p tcp -m multiport --dports 80,443 \\\n  -m conntrack --ctstate NEW -j ACCEPT\n\n# ICMP ping (rate-limited)\niptables -A INPUT -p icmp --icmp-type echo-request \\\n  -m limit --limit 1/s -j ACCEPT\n\n# Log and drop everything else\niptables -A INPUT -m limit --limit 5/min -j LOG \\\n  --log-prefix \"[iptables-DROP] \" --log-level 7\niptables -A INPUT -j DROP\n\n# Save\niptables-save > /etc/iptables/rules.v4\n```\n\n## DNAT — Port Forwarding\n\n```bash\n# Enable IP forwarding\necho 1 > /proc/sys/net/ipv4/ip_forward\nsysctl -w net.ipv4.ip_forward=1\n\n# DNAT: forward WAN port 80 to internal server 10.0.0.5:80\niptables -t nat -A PREROUTING -i eth0 -p tcp --dport 80 \\\n  -j DNAT --to-destination 10.0.0.5:80\n\n# Allow forwarded packets to reach the internal server\niptables -A FORWARD -p tcp -d 10.0.0.5 --dport 80 \\\n  -m conntrack --ctstate NEW,ESTABLISHED,RELATED -j ACCEPT\n\n# MASQUERADE: allow return traffic\niptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE\n```\n\n## Migrating to nftables\n\n```bash\n# Convert existing iptables rules automatically\niptables-save | iptables-restore-translate > /etc/nftables.conf\n\n# Or write nftables natively\n# /etc/nftables.conf\ntable inet filter {\n    chain input {\n        type filter hook input priority 0; policy drop;\n        iif \"lo\" accept\n        ct state established,related accept\n        tcp dport 22 ct state new limit rate 5/minute accept\n        tcp dport { 80, 443 } ct state new accept\n        icmp type echo-request limit rate 1/second accept\n        log prefix \"[nft-DROP] \" drop\n    }\n    chain forward { type filter hook forward priority 0; policy drop; }\n    chain output  { type filter hook output priority 0; policy accept; }\n}\n\ntable ip nat {\n    chain prerouting {\n        type nat hook prerouting priority -100;\n        iif \"eth0\" tcp dport 80 dnat to 10.0.0.5:80\n    }\n    chain postrouting {\n        type nat hook postrouting priority 100;\n        oif \"eth0\" masquerade\n    }\n}\n```\n\n```bash\nnft -f /etc/nftables.conf\nnft list ruleset\nsystemctl enable nftables\n```\n\n## Tips & Gotchas\n\n- Always test with `--check` or a cron job that flushes rules after 5 minutes — your safety net against lockouts.\n- `conntrack -L` shows the live connection tracking table — invaluable for debugging NAT.\n- `iptables-legacy` vs `iptables-nft`: on newer distros the `iptables` command may actually use an nftables backend. Check with `iptables --version`.\n- Rule ordering is critical: place high-hit rules (ESTABLISHED,RELATED) near the top; iptables evaluates rules linearly.\n"
    },
    {
        "id": "CH-19",
        "title": "PERFORMANCE_PROFILING",
        "tags": ["PERF", "FLAMEGRAPH", "STRACE", "VMSTAT"],
        "difficulty": "ADVANCED [###]",
        "category": "PERFORMANCE",
        "description": "Diagnose performance problems systematically. Use vmstat and iostat to spot resource bottlenecks, strace to understand what a process is doing, and perf with FlameGraphs to find hot code paths.",
        "objectives": [
            "Identify whether a slow application is CPU-bound, I/O-bound, or network-bound",
            "Use strace to find why a process is slow without source code",
            "Generate a FlameGraph from perf record output"
        ],
        "markdown": "## Overview\n\nPerformance debugging is a systematic process of elimination. You work top-down: system → process → function → line. Jumping straight to code before confirming where the bottleneck is wastes hours.\n\n## The USE Method\n\nFor every resource (CPU, memory, disk, network), check:\n- **U**tilization — how busy is it?\n- **S**aturation — is there a queue building up?\n- **E**rrors — are there failures?\n\n## System-Level Tools\n\n```bash\n# CPU and memory overview (update every 1 second)\nvmstat 1\n# Key columns: r (run queue), b (blocked), us (user%), sy (system%), wa (iowait%), id (idle%)\n\n# Per-CPU breakdown\nmpstat -P ALL 1\n\n# Disk I/O\niostat -xz 1\n# Key columns: %util, await (ms latency), r/s, w/s\n\n# Network\nsar -n DEV 1\nnetstat -s | grep -i error\n\n# Top-level process overview\ntop -H    # show threads\nhtop      # interactive, color-coded\n\n# Find what's eating CPU\npidstat 1\n```\n\n## Identifying Bottleneck Type\n\n```bash\n# CPU-bound: high %usr or %sys in vmstat, low %wa\n# I/O-bound: high %wa (iowait), high await in iostat\n# Memory pressure: high page faults, si/so (swap in/out) > 0 in vmstat\n# Network: high retransmit rate, dropped packets in netstat -s\n\n# For a specific process:\npidstat -u -d -t -p <PID> 1    # CPU, disk, threads\ncat /proc/<PID>/io             # cumulative I/O counters\n```\n\n## strace — System Call Tracing\n\n```bash\n# Attach to a running process and see every syscall\nstrace -p <PID> -f\n\n# Summary: which calls take the most time?\nstrace -c -p <PID>\n# -c: count calls and time them\n\n# Trace only specific syscalls\nstrace -e trace=openat,read,write ls /tmp\n\n# Find why a process is slow (filter for long calls)\nstrace -T -p <PID> 2>&1 | awk -F'<' '$2+0 > 0.01'\n# -T: show time spent in each call\n\n# Trace file access\nstrace -e trace=openat -p <PID> 2>&1 | grep -v 'ENOENT'\n```\n\n## perf — CPU Sampling Profiler\n\n```bash\n# Record CPU samples for 30 seconds\nperf record -F 99 -p <PID> -g -- sleep 30\n# -F 99: sample at 99 Hz (avoids lockstep with 100 Hz timer)\n# -g: capture call graphs\n\n# Summarize top functions\nperf report --stdio | head -40\n\n# Record system-wide\nperf record -F 99 -ag -- sleep 30\n\n# Count specific hardware events\nperf stat -e cache-misses,cache-references,cycles,instructions ./myapp\n```\n\n## FlameGraphs\n\n```bash\n# Install Brendan Gregg's FlameGraph tools\ngit clone https://github.com/brendangregg/FlameGraph /opt/flamegraph\n\n# Convert perf data to flamegraph\nperf script | /opt/flamegraph/stackcollapse-perf.pl > out.folded\n/opt/flamegraph/flamegraph.pl out.folded > flamegraph.svg\n\n# Open in a browser — wide bars at the bottom are the hot paths\n```\n\n## Memory Analysis\n\n```bash\n# Virtual memory stats for a process\ncat /proc/<PID>/status | grep -E 'VmRSS|VmSize|VmSwap'\n\n# Heap profiling with valgrind\nvalgrind --tool=massif --pages-as-heap=yes ./myapp\nms_print massif.out.<PID> | head -30\n\n# Check for memory leaks\nvalgrind --leak-check=full ./myapp\n```\n\n## Tips & Gotchas\n\n- Observing a process with `strace` adds ~10x overhead due to ptrace stop/start per syscall — don't leave it on in production.\n- `perf` requires kernel symbols (`CONFIG_KALLSYMS`) and may need `sysctl kernel.perf_event_paranoid=-1` on locked-down systems.\n- Load averages measure *run queue length*, not CPU utilization. On a 4-core system, a load of 4.0 means full saturation, not necessarily 100% CPU.\n- For JVM or Python apps, JVM flight recorder and `py-spy` respectively give language-level flamegraphs without perf.\n"
    },
    {
        "id": "CH-20",
        "title": "GIT_INTERNALS",
        "tags": ["OBJECTS", "REFS", "REBASE", "BISECT"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "VERSION_CONTROL",
        "description": "Go beyond git add and commit. Understand the object model (blobs, trees, commits, tags), manipulate history with rebase and reflog, bisect bugs to their introducing commit, and recover from disasters.",
        "objectives": [
            "Use git cat-file to inspect the raw object behind a commit",
            "Use git bisect to find the commit that introduced a bug",
            "Recover commits after an accidental git reset --hard using reflog"
        ],
        "markdown": "## Overview\n\nGit stores everything as a content-addressed object store. Understanding the four object types — blob, tree, commit, tag — explains why git is so reliable and lets you recover from situations that seem catastrophic.\n\n## The Object Model\n\n```\nCommit\n  └── Tree (/)  \n        ├── Blob (README.md)\n        ├── Blob (Makefile)\n        └── Tree (src/)\n              ├── Blob (main.c)\n              └── Blob (util.c)\n```\n\nEvery object is stored under `.git/objects/` named by its SHA-1 hash.\n\n```bash\n# Inspect any object\ngit cat-file -t HEAD            # type: commit\ngit cat-file -p HEAD            # print contents\ngit cat-file -p HEAD^{tree}     # the root tree\ngit cat-file -p HEAD:README.md  # a blob directly\n\n# Find the SHA of an object\ngit rev-parse HEAD\ngit rev-parse HEAD~3            # 3 commits back\ngit rev-parse HEAD:src/main.c   # blob SHA\n\n# Walk the object graph manually\ncommit_sha=$(git rev-parse HEAD)\ngit cat-file -p $commit_sha     # shows tree SHA, parent SHA, author\n```\n\n## Reflog — Your Safety Net\n\nThe reflog records every position HEAD has pointed to, including after resets.\n\n```bash\n# View reflog\ngit reflog\ngit reflog show --all | head -20\n\n# Recover after git reset --hard\ngit reflog                          # find the SHA before the reset\ngit reset --hard HEAD@{3}           # jump back to it\n# or cherry-pick just specific commits:\ngit cherry-pick <lost_sha>\n\n# Recover a deleted branch\ngit reflog | grep 'checkout: moving from my-feature'\ngit checkout -b my-feature <sha>\n```\n\n## Rebase — Rewriting History\n\n```bash\n# Squash the last 3 commits into one\ngit rebase -i HEAD~3\n# In the editor: change 'pick' to 'squash' (or 's') for commits to merge\n\n# Reword a commit message 5 commits back\ngit rebase -i HEAD~5\n# Change 'pick' to 'reword' on the target commit\n\n# Rebase a feature branch onto main (cleaner than merge)\ngit checkout feature/login\ngit rebase main\n# Resolve conflicts if any, then:\ngit rebase --continue\n\n# Interactive rebase with exec — run tests after each commit\ngit rebase -i HEAD~5 --exec 'make test'\n```\n\n## git bisect — Binary Search for Bugs\n\n```bash\n# Start a bisect session\ngit bisect start\ngit bisect bad                     # current commit is broken\ngit bisect good v2.3.0             # this tag was known-good\n\n# git checks out the midpoint — test it, then tell git the result\n./run_tests.sh && git bisect good || git bisect bad\n# Repeat until git identifies the first bad commit\n\n# Automate with a test script (exit 0 = good, exit 1 = bad)\ngit bisect run ./test_for_bug.sh\n\n# End the session\ngit bisect reset\n```\n\n## Useful Advanced Commands\n\n```bash\n# Find which commit introduced a string\ngit log -S 'the_function_name' --oneline\n\n# Show all commits that touched a specific file\ngit log --follow -p -- path/to/file\n\n# Stash with a name\ngit stash push -m \"WIP: new auth flow\"\ngit stash list\ngit stash pop stash@{1}\n\n# Clean untracked files (dry run first!)\ngit clean -nfd        # show what would be deleted\ngit clean -fd         # actually delete\n\n# Garbage collect and verify integrity\ngit gc --prune=now\ngit fsck --full\n```\n\n## Tips & Gotchas\n\n- Never rebase commits that have been pushed to a shared branch — it rewrites SHA history and causes divergence for other contributors.\n- `git reflog` only covers local operations. Remote-only loss (force-push) requires restoring from a backup.\n- `git worktree add ../hotfix main` lets you check out a second branch in a separate directory without stashing.\n- `GIT_TRACE=1 git <command>` reveals exactly what git is doing internally — great for debugging hooks and config issues.\n"
    },
    {
        "id": "CH-21",
        "title": "DNS_DEEP_DIVE",
        "tags": ["BIND", "ZONE_FILES", "DNSSEC", "DIG"],
        "difficulty": "ADVANCED [###]",
        "category": "NETWORKING",
        "description": "Understand DNS from the resolver to the authoritative server. Read and write zone files, set up a BIND9 authoritative server, trace resolution with dig, and implement DNSSEC to protect against spoofing.",
        "objectives": [
            "Write a zone file for a domain with A, MX, CNAME, and TXT records",
            "Set up BIND9 as an authoritative nameserver for a test domain",
            "Trace a full DNS resolution chain with dig +trace"
        ],
        "markdown": "## Overview\n\nDNS translates human-readable names into IP addresses through a distributed, hierarchical, cached database. Misconfigurations cause mysterious application failures. Understanding the full resolution chain makes you fast at diagnosing them.\n\n## The Resolution Chain\n\n```\nClient\n  → Recursive resolver (8.8.8.8)\n      → Root nameserver (.)\n          → TLD nameserver (.com)\n              → Authoritative NS (ns1.example.com)\n                  → Answer: 93.184.216.34\n```\n\n```bash\n# Trace every step\ndig +trace example.com A\n\n# Query a specific nameserver directly\ndig @8.8.8.8 example.com A\n\n# All records for a domain\ndig example.com ANY\n\n# Reverse DNS (PTR)\ndig -x 93.184.216.34\n\n# Check propagation from multiple servers\nfor ns in 8.8.8.8 1.1.1.1 9.9.9.9; do\n    echo -n \"$ns: \"; dig @$ns example.com A +short\ndone\n```\n\n## Zone File Format\n\n```dns\n; /etc/bind/zones/db.example.com\n$ORIGIN example.com.\n$TTL    3600\n\n; SOA record — Start of Authority\n@   IN  SOA  ns1.example.com. admin.example.com. (\n                2024011501  ; Serial (YYYYMMDDnn)\n                3600        ; Refresh\n                900         ; Retry\n                604800      ; Expire\n                300 )       ; Negative cache TTL\n\n; Name servers\n@       IN  NS   ns1.example.com.\n@       IN  NS   ns2.example.com.\n\n; A records\n@       IN  A    93.184.216.34\nns1     IN  A    203.0.113.1\nns2     IN  A    203.0.113.2\nwww     IN  A    93.184.216.34\nmail    IN  A    93.184.216.35\n\n; CNAME\nblog    IN  CNAME  www.example.com.\n\n; MX records (lower priority number = higher priority)\n@       IN  MX  10  mail.example.com.\n@       IN  MX  20  backup-mail.example.com.\n\n; TXT records\n@       IN  TXT  \"v=spf1 ip4:93.184.216.0/24 ~all\"\n_dmarc  IN  TXT  \"v=DMARC1; p=quarantine; rua=mailto:dmarc@example.com\"\n```\n\n## BIND9 Configuration\n\n```bash\n# /etc/bind/named.conf.local\nzone \"example.com\" {\n    type master;\n    file \"/etc/bind/zones/db.example.com\";\n    allow-transfer { 203.0.113.2; };   # secondary NS only\n};\n\n# Check zone file syntax\nnamed-checkzone example.com /etc/bind/zones/db.example.com\n\n# Check overall named config\nnamed-checkconf\n\n# Reload zones without restarting\nrndc reload example.com\n\n# Flush cache\nrndc flush\n```\n\n## DNSSEC Signing\n\n```bash\n# Generate Zone Signing Key (ZSK) and Key Signing Key (KSK)\ndnssec-keygen -a ECDSAP256SHA256 -n ZONE example.com          # ZSK\ndnssec-keygen -a ECDSAP256SHA256 -n ZONE -f KSK example.com   # KSK\n\n# Add keys to zone file\ncat Kexample.com.*.key >> /etc/bind/zones/db.example.com\n\n# Sign the zone\ndnssec-signzone -A -3 $(head -c 1000 /dev/random | sha1sum | cut -b 1-16) \\\n  -N INCREMENT -o example.com -t /etc/bind/zones/db.example.com\n\n# Publish DS record to parent zone registrar\ncat Kexample.com.*key.ds\n\n# Verify DNSSEC\ndig +dnssec example.com A\ndig DNSKEY example.com\ndelv @8.8.8.8 example.com A +rtrace    # end-to-end DNSSEC validation\n```\n\n## Common DNS Record Types\n\n| Type | Purpose | Example |\n|------|---------|----------|\n| A | IPv4 address | `www → 93.184.216.34` |\n| AAAA | IPv6 address | `www → 2606:2800:220:1:..` |\n| CNAME | Canonical name alias | `blog → www` |\n| MX | Mail exchanger | `@ → mail.example.com` |\n| TXT | Freeform text | SPF, DKIM, DMARC, verification |\n| NS | Nameserver delegation | `@ → ns1.example.com` |\n| PTR | Reverse DNS | `34.216.184.93.in-addr.arpa → www` |\n| SRV | Service location | `_http._tcp → host:port:priority` |\n| CAA | CA authorization | `@ → letsencrypt.org` |\n\n## Tips & Gotchas\n\n- Always increment the SOA serial number when modifying a zone — secondaries use it to detect changes.\n- TTL is a *hint* to resolvers, not a hard guarantee. Lowering TTL before a migration gives you faster rollback but increases query load.\n- `dig +short` is your friend for scripts, but always use the verbose form when debugging.\n- CAA records prevent unauthorized CAs from issuing certs for your domain — add one if you use Let's Encrypt: `0 issue \"letsencrypt.org\"`.\n"
    },
    {
        "id": "CH-22",
        "title": "BACKUP_STRATEGIES",
        "tags": ["RSYNC", "RESTIC", "3-2-1", "RESTORE"],
        "difficulty": "INTERMEDIATE [##-]",
        "category": "DISASTER_RECOVERY",
        "description": "Build a backup system you'd actually trust. Implement the 3-2-1 rule with rsync for efficient differentials and restic for encrypted, deduplicated backups. Practice restores — because untested backups aren't backups.",
        "objectives": [
            "Set up incremental backups using rsync with --link-dest for hard-link deduplication",
            "Configure restic to back up to an S3-compatible bucket with encryption",
            "Simulate a disaster recovery scenario and verify restore integrity"
        ],
        "markdown": "## Overview\n\nThe 3-2-1 rule: **3** copies of data, on **2** different media types, with **1** offsite. Backups are only as good as your last successful restore test. This challenge covers practical implementation from local incrementals to encrypted cloud backups.\n\n## rsync for Efficient Incrementals\n\n```bash\n# Basic rsync backup\nrsync -avz --progress /source/ user@backup-host:/destination/\n\n# Key flags\n# -a: archive (recursive + preserve permissions, timestamps, symlinks)\n# -z: compress in transit\n# --delete: remove files at destination that no longer exist at source\n# --exclude: skip patterns\n\n# Hard-link incremental backups (snapshot-style, disk-efficient)\nDATE=$(date +%Y-%m-%d_%H%M%S)\nLATEST=/backup/latest\nDEST=/backup/$DATE\n\nrsync -avz --delete \\\n  --link-dest=\"$LATEST\" \\\n  --exclude='*.tmp' \\\n  --exclude='/proc' \\\n  /source/ \"$DEST/\"\n\n# Update the 'latest' symlink\nrm -f \"$LATEST\"\nln -s \"$DEST\" \"$LATEST\"\n\n# Each snapshot appears full but shares unchanged inodes — very space-efficient\ndu -sh /backup/2024-01-1*/   # all appear full-sized\ndu -sh /backup/              # actual disk usage is much smaller\n```\n\n## restic — Encrypted, Deduplicated Backups\n\n```bash\n# Install\napt install restic\n\n# Initialize a local repository\nrestic init --repo /mnt/backup/restic-repo\n\n# Initialize an S3 repository (MinIO or AWS)\nexport AWS_ACCESS_KEY_ID=xxx\nexport AWS_SECRET_ACCESS_KEY=xxx\nexport RESTIC_REPOSITORY=\"s3:https://s3.amazonaws.com/my-backup-bucket\"\nexport RESTIC_PASSWORD=\"my_strong_passphrase\"\nrestic init\n\n# Run a backup\nrestic backup /home /etc /var/www \\\n  --exclude='*.log' \\\n  --exclude='/home/*/.cache'\n\n# List snapshots\nrestic snapshots\n\n# Show what's in a snapshot\nrestic ls latest\nrestic ls 3a7e4f2d /etc\n\n# Restore a full snapshot\nrestic restore latest --target /tmp/restore\n\n# Restore a single file\nrestic restore latest --target /tmp/restore --include '/etc/nginx/nginx.conf'\n\n# Verify data integrity\nrestic check\nrestic check --read-data    # actually reads all pack files (slow but thorough)\n\n# Prune old snapshots\nrestic forget --keep-daily 7 --keep-weekly 4 --keep-monthly 12 --prune\n```\n\n## Retention Policies\n\n```bash\n# Example policy: 7 daily, 4 weekly, 12 monthly, 2 yearly\nrestic forget \\\n  --keep-daily   7 \\\n  --keep-weekly  4 \\\n  --keep-monthly 12 \\\n  --keep-yearly  2 \\\n  --prune\n\n# Automate with systemd timer\n# /etc/systemd/system/restic-backup.service\n[Unit]\nDescription=Restic backup\n\n[Service]\nType=oneshot\nEnvironmentFile=/etc/restic/env    # store credentials here, chmod 600\nExecStart=restic backup /home /etc\nExecStartPost=restic forget --keep-daily 7 --keep-weekly 4 --prune\n\n# /etc/systemd/system/restic-backup.timer\n[Timer]\nOnCalendar=*-*-* 02:00:00\nPersistent=true\n\n[Install]\nWantedBy=timers.target\n```\n\n## Disaster Recovery Drill\n\n```bash\n# Simulate: list what you'd need to restore\nrestic snapshots\nrestic ls latest --long | head -20\n\n# Restore to an isolated test directory\nmkdir /tmp/dr-test\nrestic restore latest --target /tmp/dr-test\n\n# Verify file count and checksums\nfind /source -type f | wc -l\nfind /tmp/dr-test/source -type f | wc -l\n\n# Deep verification with checksums\nfind /source -type f -exec sha256sum {} \\; | sort > /tmp/source.sha\nfind /tmp/dr-test -type f -exec sha256sum {} \\; | \\\n  sed 's|/tmp/dr-test||' | sort > /tmp/restore.sha\ndiff /tmp/source.sha /tmp/restore.sha\n```\n\n## Tips & Gotchas\n\n- Store the restic repository password and encryption key somewhere physically separate from the backup — losing the key means losing the data.\n- Test restores quarterly at minimum. Backup systems silently fail all the time.\n- `rsync --dry-run -v` shows exactly what would be changed before committing.\n- For databases (PostgreSQL, MySQL), always dump to a flat file before rsync — copying live database files produces inconsistent backups.\n"
    }
]
