FROM python:3.14.0-slim-bookworm
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_DISABLE_PIP_VERSION_CHECK=1
WORKDIR /app
COPY pyproject.toml uv.lock README.md ./
RUN pip install --no-cache-dir uv==0.8.22 && uv sync --frozen --no-dev
COPY . .
ENV PATH="/app/.venv/bin:$PATH" PYTHONPATH=/app/src:/app
RUN addgroup --system serviceops && adduser --system --ingroup serviceops serviceops && chown -R serviceops:serviceops /app
USER serviceops
CMD ["uvicorn", "serviceops.api.app:app", "--host", "0.0.0.0", "--port", "8000"]

