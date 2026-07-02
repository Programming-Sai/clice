# clice

A sandboxed CLI evaluation platform that measures not just what you solved — but how.

for now run cli with:

```bash
docker ps -a | grep clice | awk '{print $1}' | xargs -r docker rm -f && docker volume ls | grep clice-workspace | awk '{print $2}' | xargs -r docker volume rm -f && python clice.py run hello-clice
```

and run textual tui with:

```psh
python -m ui.main
```

> [!NOTE]
> Now you would need to run both the tui and the cli in a linux or with wsl
> Current design allows that if there is an interruption during a session and you comeback it continues. however if you pass or fail (Basically get to the verdict screen, your progress is reset.)
