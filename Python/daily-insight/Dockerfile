FROM python:3.10-slim

WORKDIR /app

# git is needed to pip-install railtracks from its pinned commit (see
# pyproject.toml). Remove once we move back to a PyPI-released version.
RUN apt-get update \
    && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*

# Install the package + deps. Copying pyproject.toml + src separately lets
# Docker cache the dependency install across source-only changes.
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "daily_insight.controllers.api:app", "--host", "0.0.0.0", "--port", "8000"]
