from datetime import UTC, datetime, timedelta

from airflow import DAG
from airflow.providers.standard.operators.python import PythonOperator

from webshop.pipelines.sessionization import SessionizationPipeline
from webshop.utils.database import DatabaseConnection
from webshop.utils.storage import GCSClient
import os

default_args = {
    "owner": "data-team",
    "depends_on_past": False,
    "start_date": datetime(2024, 1, 1, tzinfo=UTC),
    "email_on_failure": True,
    "email_on_retry": False,
    "retries": 0,
    "retry_delay": timedelta(minutes=5),
}

dag = DAG(
    "webshop_analytics",
    default_args=default_args,
    description="Process webshop events and generate analytics",
    schedule="@daily",
    catchup=False,
)


def run_sessionization(**context):
    os.environ["DB_HOST"] = "postgres"
    os.environ["DB_USER"] = "airflow"
    os.environ["DB_PASSWORD"] = "airflow"

    db = DatabaseConnection()
    db.init_database()
    storage_client = GCSClient()
    pipeline = SessionizationPipeline(db, storage_client)
    date = context["ds"]
    return pipeline.run(date)


sessionization_task = PythonOperator(
    task_id="sessionization",
    python_callable=run_sessionization,
    dag=dag,
)
