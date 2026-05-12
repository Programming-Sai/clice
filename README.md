# clice

A sandboxed CLI evaluation platform that measures not just what you solved — but how.

for now run with:

```bash
docker ps -a | grep clice | awk '{print $1}' | xargs -r docker rm -f && docker volume ls | grep clice-workspace | awk '{print $2}' | xargs -r docker volume rm -f && python clice.py run hello-clice
```

> [!NOTE]
> Use WSL
