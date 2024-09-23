# Copyright © 2024 Province of British Columbia
#
# Licensed under the Apache License, Version 2.0 (the 'License');
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an 'AS IS' BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""API endpoints for managing a submission resource."""

from http import HTTPStatus

from flask_restx import Namespace, Resource, cors

from epic_document_api.auth import auth
from epic_document_api.schemas.fileobject import BlobObject, BlobObjectRequest
from epic_document_api.services.object_storage_service import ObjectStorageService
from epic_document_api.utils.util import cors_preflight

from .apihelper import Api as ApiHelper


API = Namespace('objects', description='Endpoints for Submission Management')
"""Custom exception messages
"""

object_request_model = ApiHelper.convert_ma_schema_to_restx_model(
    API, BlobObjectRequest(), 'An object to upload'
)

object_response_model = ApiHelper.convert_ma_schema_to_restx_model(
    API, BlobObject(), 'An object with auth headers'
)


@cors_preflight('GET, OPTIONS, POST')
@API.route('', methods=['POST', 'GET', 'OPTIONS'])
class ObjectAuthHeaders(Resource):
    """Resource for managing objects s3 auth headers."""

    @staticmethod
    @ApiHelper.swagger_decorators(API, endpoint_description='Get s3 auth headers for object')
    @API.expect(object_request_model)
    @API.response(
        code=HTTPStatus.CREATED, model=object_response_model, description='File with s3 auth headers'
    )
    @API.response(HTTPStatus.BAD_REQUEST, 'Bad Request')
    # @auth.require
    @cors.crossdomain(origin='*')
    def post():
        """Get auth headers."""
        request_file = BlobObjectRequest().load(API.payload)
        file = ObjectStorageService().apply_auth_headers(request_file)
        return BlobObject().dump(file), HTTPStatus.OK
