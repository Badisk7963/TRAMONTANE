FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml .
COPY tramontane/ tramontane/
COPY pipelines/ pipelines/

RUN uv sync --no-dev

RUN useradd -m -u 1000 tramontane && chown -R tramontane /app
USER tramontane

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=5s \
  CMD python -c "import httpx; httpx.get('http://localhost:8080/health')"

CMD ["uvicorn", "tramontane.server.app:create_app", \
     "--factory", "--host", "0.0.0.0", "--port", "8080"]
