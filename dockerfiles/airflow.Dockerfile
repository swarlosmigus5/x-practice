FROM apache/airflow:3.0.4

WORKDIR /app

COPY ./readme.md ./readme.md
COPY ./pyproject.toml ./pyproject.toml
COPY ./uv.lock ./uv.lock
COPY ./src ./src

RUN pip install .

WORKDIR /opt/airflow
