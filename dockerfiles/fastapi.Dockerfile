FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*


COPY ./readme.md ./readme.md
COPY ./pyproject.toml ./pyproject.toml
COPY ./uv.lock ./uv.lock
COPY ./src ./src

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app

CMD ["uvicorn", "webshop.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
