# Known issues (internal tracking, not for the README)

## Orphaned container on interrupt inside load_challenge()

**Status:** Documented, not fixed. Low priority, come back to later.

`cmd_run()` in `clice.py` catches `KeyboardInterrupt`/`EOFError` around both
the container-startup phase and the interactive command loop, calling
`loader.cleanup(container)` in each case. This closes the two main windows
where an interrupt could orphan a container.

There's still one narrow gap: if the interrupt lands _inside_
`ChallengeLoader.load_challenge()` (in `loader/challenge_loader.py`) -
specifically after Docker's `containers.run()` has already succeeded but
before that function returns control to its caller - the container will
exist in Docker, but `cmd_run()` never receives a reference to it to clean
up, since the exception unwinds before the `container = loader.load_challenge(...)`
assignment completes.

**Why it's not fixed yet:** closing this properly means `load_challenge()`
itself needs to track and clean up its own partially-created container on
an interrupt/exception, rather than relying entirely on the caller - that's
a real (if small) piece of work inside `challenge_loader.py`, not a one-line
fix at the call site.

**How to actually verify/reproduce:** send SIGINT with very precise timing
right around the `containers.run()` call inside `load_challenge()` - hard to
hit reliably by hand, would need either a debugger breakpoint or an
artificial delay inserted right after `containers.run()` to widen the
window enough to interrupt reliably.
