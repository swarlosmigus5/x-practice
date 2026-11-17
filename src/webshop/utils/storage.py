import json
import logging
import os

from google.cloud import storage

logger = logging.getLogger(__name__)


class GCSClient:
    """Google Cloud Storage client."""

    def __init__(self):
        self.bucket_name = os.getenv("GCS_BUCKET", "xcc-de-assessment")
        self.client = storage.Client.create_anonymous_client()
        self.bucket = self.client.bucket(self.bucket_name)

    def download_events(self, date: str = None) -> list[str]:
        """Download events from GCS."""
        blob_name = "events.json"

        blob = self.bucket.blob(blob_name)

        # Download to string
        content = blob.download_as_text()

        # Split by newlines for JSONL format
        events = content.strip().split("\n")

        logger.info(f"Downloaded {len(events)} events from GCS")

        return events

    def upload_results(self, data: dict, filename: str):
        """Upload results to GCS."""
        blob = self.bucket.blob(f"results/{filename}")
        blob.upload_from_string(json.dumps(data))
        logger.info(f"Uploaded results to {filename}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    GCSClient().download_events()
