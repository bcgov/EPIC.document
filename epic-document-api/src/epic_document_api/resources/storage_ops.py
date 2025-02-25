"""Operations related to the storage."""

from http import HTTPStatus

from flask import request
from flask_restx import Namespace, Resource, cors

from epic_document_api.schemas.storage_ops import PresignedUrlRequestSchema, PresignedUrlResponseSchema
from epic_document_api.services.object_storage_service import ObjectStorageService
from epic_document_api.utils.util import cors_preflight

from .apihelper import Api as ApiHelper


API = Namespace("storage-operations", description="Operations on the cloud storage")

pre_signed_url_request = ApiHelper.convert_ma_schema_to_restx_model(
    API, PresignedUrlRequestSchema(), "Parameters to get presigned url"
)
pre_signed_url_response = ApiHelper.convert_ma_schema_to_restx_model(
    API, PresignedUrlResponseSchema(), "Response of presigned url request"
)


@cors_preflight("OPTIONS, POST")
@API.route("/presigned-urls", methods=["POST", "OPTIONS"])
class PresignedURLs(Resource):
    """PresignedURL Resource."""

    @staticmethod
    @ApiHelper.swagger_decorators(
        API, endpoint_description="Get presiged urls for uploading files"
    )
    @API.doc(
        params={
            "public-read": {
                "description": "true if you need the url to let you put a file which is available publicaly",
                "type": "boolean",
                "required": False,
            },
            "expires": {
                "description": "The number of seconds the url to be valid limited by 600 seconds",
                "type": "integer",
                "required": False,
            },
        }
    )
    @API.expect(pre_signed_url_request)
    @API.response(
        code=HTTPStatus.OK,
        model=pre_signed_url_response,
        description="File with s3 auth headers",
    )
    @API.response(HTTPStatus.BAD_REQUEST, "Bad Request")
    @cors.crossdomain(origin="*")
    def post():
        """Get presigned urls."""
        payload = PresignedUrlRequestSchema().load(API.payload)
        additional_headers = request.args | {}
        response = ObjectStorageService().generate_presigned_urls(
            payload, additional_headers
        )
        return PresignedUrlResponseSchema().dump(response), HTTPStatus.OK
