$ErrorActionPreference = 'Stop'
docker compose build
docker compose up -d db operations-db operations-api
docker compose run --rm web alembic upgrade head
docker compose run --rm web python scripts/seed.py
docker compose up -d web worker
docker compose ps

