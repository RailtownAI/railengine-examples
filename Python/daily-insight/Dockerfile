FROM python:3.10-slim

WORKDIR /app

# Install the package + deps. Copying pyproject.toml + src separately lets
# Docker cache the dependency install across source-only changes.
COPY pyproject.toml ./
COPY src/ ./src/
RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "daily_insight.controllers.api:app", "--host", "0.0.0.0", "--port", "8000"]
