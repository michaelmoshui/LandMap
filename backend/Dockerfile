# syntax=docker/dockerfile:1

# ---- base: runtime deps only -------------------------------------------
FROM python:3.12-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt
COPY app ./app

# ---- test: adds dev/test deps + tests; default runs the suite ----------
FROM base AS test
COPY requirements-dev.txt pyproject.toml ./
RUN pip install -r requirements-dev.txt
COPY tests ./tests
CMD ["pytest"]

# ---- prod: minimal image running uvicorn -------------------------------
FROM base AS prod
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
