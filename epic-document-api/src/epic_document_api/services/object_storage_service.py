"""Service for object storage management."""

import os
import uuid
from typing import Dict

import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from flask import current_app
from markupsafe import string

from epic_document_api.models import Document as DocumentModel
from epic_document_api.schemas.storage_ops import ActionOnFileEnum
from epic_document_api.utils.boto_factory import Boto3ClientFactory


class ObjectStorageService:
    """Object storage management service."""

    def __init__(self):
        """Initialize the service."""
        # initialize s3 config from environment variables
        self.s3_access_key_id = current_app.config.get("S3_ACCESS_KEY_ID")
        self.s3_secret_access_key = current_app.config.get("S3_SECRET_ACCESS_KEY")
        self.s3_host = current_app.config.get("S3_HOST")
        self.s3_bucket = current_app.config.get("S3_BUCKET")
        self.s3_region = current_app.config.get("S3_REGION")
        self.s3_service = current_app.config.get("S3_SERVICE")
        self.s3_client = Boto3ClientFactory(
            endpoint_url=f"https://{current_app.config.get('S3_HOST')}"
        ).get_client("s3")

    def get_url(self, filename: string, folder: string = "") -> string:
        """Get the object url."""
        if not all([self.s3_host, self.s3_bucket, filename]):
            return ""

        if folder:
            folder = folder.strip("/")
            folder = f"/{folder}/"
        else:
            folder = "/"

        return f"https://{self.s3_host}/{self.s3_bucket}{folder}{filename}"

    def delete_s3_object(self, file: Dict) -> Dict:
        """Delete the S3 object."""
        self._check_s3_configuration()
        s3_source_uri = file.get("filepath")

        auth = self._create_aws_auth()
        response = self._make_s3_auth_headers_request(s3_source_uri, "", auth)
        auth_headers = response.request.headers
        self._make_s3_delete_request(s3_source_uri, auth, auth_headers)
        document = DocumentModel.get_by_path(s3_source_uri)
        if document:
            document.delete()
        return file

    def generate_presigned_urls(self, payload: dict):
        """Generate presigned URL based on the given file information."""
        action = payload.get("action")
        relative_url = payload.get("relative_url")
        folder, filename = os.path.split(relative_url)
        project_id = payload.get("project_id", None)
        if action == ActionOnFileEnum.PUT:
            pre_signed_url, key = self._generate_presigned_put(
                folder, filename, project_id
            )
        elif action == ActionOnFileEnum.DELETE:
            pre_signed_url, key = self._generate_presigned_delete(relative_url)
        else:
            raise ValueError("Invalid action specified.")
        return {"presigned_url": pre_signed_url, "relative_url": key}

    def _generate_presigned_put(self, folder, filename, project_id=None):
        """Generate presigned put url."""
        unique_filename = self._generate_unique_filename(filename)
        key = f"{folder.strip('/')}/{unique_filename}"
        pre_signed_url = self.s3_client.generate_presigned_url(
            ActionOnFileEnum.PUT.value,
            Params={"Bucket": self.s3_bucket, "Key": key},
            ExpiresIn=300,
        )
        document = DocumentModel(
            **{
                "name": filename,
                "unique_name": unique_filename,
                "path": key,
                "project_id": project_id,
            }
        )
        document.save()
        return pre_signed_url, key

    def _generate_presigned_delete(self, relative_url):
        """Generate presigned delete."""
        key = relative_url
        pre_signed_url = self.s3_client.generate_presigned_url(
            ActionOnFileEnum.DELETE.value,
            Params={"Bucket": self.s3_bucket, "Key": key},
            ExpiresIn=300,
        )
        document = DocumentModel.get_by_path(key)
        if document:
            document.delete()
        return pre_signed_url, key

    @staticmethod
    def _make_s3_delete_request(s3_source_uri: str, auth, auth_headers):
        """Make the appropriate S3 request."""
        headers = {
            "x-amz-date": auth_headers.get("x-amz-date"),
            "Authorization": auth_headers.get("Authorization"),
        }
        return requests.delete(s3_source_uri, auth=auth, headers=headers)

    def apply_auth_headers(self, file: Dict) -> Dict:
        """Get the S3 auth headers for the provided files."""
        self._check_s3_configuration()
        s3_source_uri = file.get("s3sourceuri")
        unique_filename = self._generate_unique_filename(file.get("filename", ""))
        folder = file.get("folder", "")

        auth = self._create_aws_auth()
        s3_uri = self._get_s3_uri(s3_source_uri, unique_filename, folder)
        response = self._make_s3_auth_headers_request(s3_uri, s3_source_uri, auth)

        self._update_file_with_response(
            file, s3_uri, response, unique_filename, s3_source_uri
        )
        self._save_file_record(file, unique_filename)

        return file

    def _check_s3_configuration(self):
        """Check for missing S3 configuration."""
        if not all(
            [
                self.s3_access_key_id,
                self.s3_secret_access_key,
                self.s3_host,
                self.s3_bucket,
            ]
        ):
            raise ValueError("Missing S3 configuration")

    @staticmethod
    def _generate_unique_filename(filename: str) -> str:
        """Generate a unique filename."""
        filename_split_text = os.path.splitext(filename)
        return f"{uuid.uuid4()}{filename_split_text[1]}"

    def _create_aws_auth(self) -> AWSRequestsAuth:
        """Create AWS authentication object."""
        return AWSRequestsAuth(
            aws_access_key=self.s3_access_key_id,
            aws_secret_access_key=self.s3_secret_access_key,
            aws_host=self.s3_host,
            aws_region=self.s3_region,
            aws_service=self.s3_service,
        )

    @staticmethod
    def _update_file_with_response(
        file: Dict,
        s3_uri: str,
        response: requests.Response,
        unique_filename: str,
        s3_source_uri: str,
    ):
        """Update the file dictionary with response data."""
        file.update(
            {
                "filepath": s3_uri,
                "authheader": response.request.headers.get("Authorization"),
                "amzdate": response.request.headers.get("x-amz-date"),
                "uniquefilename": unique_filename if not s3_source_uri else "",
            }
        )

    @staticmethod
    def _save_file_record(file: Dict, unique_filename: str):
        """Save the file record to the database."""
        saved_file = DocumentModel(
            name=file.get("filename"),
            unique_name=unique_filename,
            path=file.get("filepath"),
        )
        saved_file.save()

    def _get_s3_uri(self, s3_source_uri: str, unique_filename: str, folder: str) -> str:
        """Generate the S3 URI."""
        return s3_source_uri or self.get_url(unique_filename, folder)

    @staticmethod
    def _make_s3_auth_headers_request(
        s3_uri: str, s3_source_uri: str, auth: AWSRequestsAuth
    ) -> requests.Response:
        """Make the appropriate S3 request."""
        if s3_source_uri:
            return requests.get(s3_uri, auth=auth)
        return requests.put(s3_uri, data=None, auth=auth)
