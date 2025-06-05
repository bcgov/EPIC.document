"""Shema for operations request and responses."""

from enum import Enum

from marshmallow import Schema, fields
from marshmallow_enum import EnumField

from .base_schema import BaseSchema


class ActionOnFileEnum(Enum):
    """Action that can be performed on the file in cloud storage."""

    PUT = "put_object"
    DELETE = "delete_object"
    GET = "get_object"


class PresignedUrlRequestSchema(BaseSchema):
    """Request schema for presigned URL."""

    action = EnumField(
        ActionOnFileEnum,
        metadata={"description": "The actions that can be performed on the file."},
        missing=ActionOnFileEnum.PUT,
    )
    relative_url = fields.Str(
        metadata={
            "description": "The relative url of the file in which it is supposed to be stored in the storage location"
        },
        required=True,
    )
    project_id = fields.Int(
        metadata={
            "description": "The unique identifier of the project associated with the file"
        },
        allow_none=True,
    )


class PresignedUrlResponseSchema(Schema):
    """PresignedUrlResponseSchema."""

    presigned_url = fields.Str(metadata={"description": "Presigned URL"})
    relative_url = fields.Str(
        metadata={"description": "The relative path of the file in the storage"}
    )


class ObjectOperationRequestSchema(BaseSchema):
    """Schema for performing operations on an S3 object."""

    action = fields.Str(
        metadata={"description": "The operation to perform (e.g., 'copy', 'move', 'delete')"},
        required=True,
    )
    source_folder = fields.Str(
        metadata={"description": "The source folder where the object is located"},
        required=False,
        allow_none=True,
    )
    filename = fields.Str(
        metadata={"description": "The name of the file to operate on"},
        required=True,
    )
    relative_url = fields.Str(
        metadata={"description": "The relative URL of the file in the storage"},
        required=True,
    )
    destination_folder = fields.Str(
        metadata={"description": "The destination folder (if applicable)"},
        required=False,
        allow_none=True,
    )
