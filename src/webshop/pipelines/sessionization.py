import json
import logging
from datetime import timedelta
from webshop.utils.storage import GCSClient
from webshop.utils.database import DatabaseConnection
from typing import Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


class SessionizationPipeline:
    def __init__(self, db_connection, storage_client, session_timeout_minutes=30):
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.db = db_connection
        self.storage = storage_client

    def run(self, date: str):
        logger.info(f"Starting sessionization pipeline for date: {date}")

        try:
            events = self.storage.download_events(date)
            # with Path.open("events.json", "r") as f:
            #     events = f.readlines()

            flattened_df = pd.json_normalize(
                pd.DataFrame(events)
                .assign(
                    parsed_event=lambda df: df[0].apply(json.loads),
                )["parsed_event"],
            )

            sessions = (
                flattened_df
                .pipe(
                    lambda df: df.dropna(subset=["event.customer-id"]),
                )
                .assign(
                    customer_id=lambda df: df["event.customer-id"],
                    timestamp=lambda df: pd.to_datetime(df["event.timestamp"]),
                )
                .sort_values(["customer_id", "timestamp"])
                .pipe(self._create_session_windows, date)
                .pipe(self._aggregate_sessions)
                .to_dict("records")
            )

            self.save_sessions_atomic(sessions, date)

            logger.info(
                f"Successfully processed {len(sessions)} sessions for date: {date}"
            )
            return len(sessions)

        except Exception:
            logger.exception("Pipeline failed for date %s" % date)
            raise

    def _create_session_windows(self, df: pd.DataFrame, date: str) -> pd.DataFrame:
        return df.assign(
            time_diff=lambda d: d.groupby("customer_id")["timestamp"].transform("diff"),
            session_break=lambda d: (d.time_diff > self.session_timeout).fillna(True),
            session_num=lambda d: d.groupby("customer_id")["session_break"].transform(
                "cumsum"
            ),
            session_id=lambda d: date
            + "_"
            + d.customer_id.astype(str)
            + "_"
            + d.session_num.astype(str),
        )

    def _aggregate_sessions(self, df: pd.DataFrame) -> pd.DataFrame:
        return (
            df.groupby("session_id")
            .agg(
                {
                    "customer_id": "first",
                    "timestamp": ["min", "max", "count"],
                    "type": lambda x: (x == "placed_order").any(),
                    # "parsed_event": lambda x: x.tolist(),
                },
            )
            .pipe(self._flatten_columns)
            .assign(
                duration_minutes=lambda x: (
                    x.end_time - x.start_time
                ).dt.total_seconds()
                / 60,
            )
        )

    def _flatten_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        df.columns = [
            "customer_id",
            "start_time",
            "end_time",
            "event_count",
            "has_order",
        ]
        return df.reset_index()

    def save_sessions_atomic(self, sessions: List[Dict], date: str):
        conn = self.db.get_connection()

        try:
            conn.autocommit = False
            cursor = conn.cursor()

            delete_query = """
                DELETE FROM sessions 
                WHERE process_date = %s
            """
            cursor.execute(delete_query, (date,))
            deleted_count = cursor.rowcount

            for session in sessions:
                query = """
                    INSERT INTO sessions (
                        session_id, customer_id, start_time, end_time, 
                        duration_minutes, event_count, has_order, process_date
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """

                cursor.execute(
                    query,
                    (
                        session["session_id"],
                        session["customer_id"],
                        session["start_time"],
                        session["end_time"],
                        session["duration_minutes"],
                        session["event_count"],
                        session["has_order"],
                        date,
                    ),
                )

            conn.commit()
            logger.info(
                f"Atomically replaced {deleted_count} existing sessions with {len(sessions)} new sessions for date: {date}"
            )

        except Exception:
            conn.rollback()
            logger.exception(
                "Failed to save sessions for date %s, rolling back",
                (date),
            )
            raise
        finally:
            cursor.close()
            conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    db_connection = DatabaseConnection()
    storage_client = GCSClient()
    pipeline = SessionizationPipeline(db_connection, storage_client)
    pipeline.run("2019-01-01")
