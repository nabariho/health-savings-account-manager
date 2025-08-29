# devops
Use the `docker-containerization-specialist` subagent.
Context: ARCHITECTURE.md, CLAUDE.md, .claude/context/engineering.md.
Goals:
- Produce Dockerfile(s), .dockerignore, and docker-compose for backend + frontend.
- Ensure: non-root images, minimal layers, /health endpoint, documented env vars (OPENAI_API_KEY).
- Run `docker compose up --build`; verify /health; capture logs.
- Append run instructions and troubleshooting to README and PROJECT_ROADMAP.md.
  Rules: keep images small; never bake secrets into images.
