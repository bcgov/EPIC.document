"""Service for object storage management."""
import os
import uuid
from typing import Dict

import requests
from aws_requests_auth.aws_auth import AWSRequestsAuth
from flask import current_app
from markupsafe import string

from epic_document_api.models import Document


class ObjectStorageService:
    """Object storage management service."""

    def __init__(self):
        """Initialize the service."""
        # initialize s3 config from environment variables
        self.s3_access_key_id = current_app.config.get('S3_ACCESS_KEY_ID')
        self.s3_secret_access_key = current_app.config.get('S3_SECRET_ACCESS_KEY')
        self.s3_host = current_app.config.get('S3_HOST')
        self.s3_bucket = current_app.config.get('S3_BUCKET')
        self.s3_region = current_app.config.get('S3_REGION')
        self.s3_service = current_app.config.get('S3_SERVICE')

    def get_url(self, filename: string):
        """Get the object url."""
        if not all([self.s3_host, self.s3_bucket, filename]):
            return ''

        return f'https://{self.s3_host}/{self.s3_bucket}/{filename}'

    def apply_auth_headers(self, file: Dict) -> Dict:
        """Get the S3 auth headers for the provided files."""
        # Check for missing S3 configuration
        print(">>>>>>> " + self.s3_service)
        if not self.s3_access_key_id:
            raise ValueError('Missing S3 Access Key ID')
        if not self.s3_secret_access_key:
            raise ValueError('Missing S3 Secret Access Key')
        if not self.s3_host:
            raise ValueError('Missing S3 Host')
        if not self.s3_bucket:
            raise ValueError('Missing S3 Bucket')

        s3_source_uri = file.get('s3sourceuri')
        filename_split_text = os.path.splitext(file.get('filename', ''))
        unique_filename = f'{uuid.uuid4()}{filename_split_text[1]}'

        auth = AWSRequestsAuth(
            aws_access_key=self.s3_access_key_id,
            aws_secret_access_key=self.s3_secret_access_key,
            aws_host=self.s3_host,
            aws_region=self.s3_region,
            aws_service=self.s3_service
        )

        s3_uri = self._get_s3_uri(s3_source_uri, unique_filename)
        response = self._make_s3_request(s3_uri, s3_source_uri, auth)

        file.update({
            'filepath': s3_uri,
            'authheader': response.request.headers.get('Authorization'),
            'amzdate': response.request.headers.get('x-amz-date'),
            'uniquefilename': unique_filename if not s3_source_uri else ''
        })

        saved_file = Document(
            name=file.get('filename'),
            unique_name=unique_filename,
            path=file.get('filepath'),
        )
        saved_file.save()

        return file

    def _get_s3_uri(self, s3_source_uri: str, unique_filename: str) -> str:
        """Generate the S3 URI."""
        return s3_source_uri or self.get_url(unique_filename)

    @staticmethod
    def _make_s3_request(s3_uri: str, s3_source_uri: str, auth: AWSRequestsAuth) -> requests.Response:
        """Make the appropriate S3 request."""
        if s3_source_uri:
            return requests.get(s3_uri, auth=auth)
        print(s3_uri)
        return requests.put(s3_uri, data=None, auth=auth)
