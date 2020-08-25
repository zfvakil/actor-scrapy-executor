from __future__ import annotations
from pydantic import validator, BaseModel
from google.cloud import storage
from typing import List, Set
import logging


GCP_PROJECT = "meetkai-3945f"
GCP_BUCKET = "meetkai-3945f-vcm"


def gcp_list_blobs():
    """Lists all the blobs in the bucket."""
    storage_client = storage.Client(project=GCP_PROJECT)

    # Note: Client.list_blobs requires at least package version 1.17.0.
    blobs = storage_client.list_blobs(GCP_BUCKET)

    for blob in blobs:
        print(blob.name)


def gcp_upload_blob(*, source_file_name: str, destination_blob_name: str) -> None:
    """Uploads a file to the bucket."""
    storage_client = storage.Client(project=GCP_PROJECT)
    bucket = storage_client.get_bucket(GCP_BUCKET)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)


def upload_gcp_batch(*, batch_inputs: List[AutoMlInput], domain: str, thread_num: int, logger: logging.Logger) -> None:
    total = len(batch_inputs)
    for ind, img_input in enumerate(batch_inputs):
        gcp_upload_blob(
            source_file_name=img_input.img_path(), destination_blob_name=f"imgs/{domain}/{img_input.file_name}"
        )
        if ind % 500 == 0:
            logger.info(f"Thread {thread_num} is {ind/total}% complete uploading to GCP")


def clean_label(*, label):
    for b in [("&", "and")]:
        label = label.replace(b[0], b[1])
    return label.lower().strip()


class AutoMlInput(BaseModel):
    file_name: str
    domain: str
    file_location: str
    labels: List[str]

    @validator("file_location", always=True)
    def proper_location(cls, v):
        if not v:
            raise ValueError("file_location cannot be empty")
        return v

    @validator("labels", whole=True, always=True)
    def proper_labels(cls, v):
        if not v:
            raise ValueError("labels cannot be empty")
        proper: List[str] = []
        for l in v:
            if not l.strip():
                raise ValueError("The labels cannot be empty")
            proper.append(l)
        return list(set(proper))

    @validator("labels", always=True)
    def proper_label(cls, v):
        if not v:
            raise ValueError("labels cannot be empty")
        return v

    def img_path(self):
        return self.file_location + "/" + self.file_name

    def csv_row(self) -> List[str]:
        return ["gs://" + GCP_BUCKET + "/imgs/" + self.domain + "/" + self.file_name] + self.labels
