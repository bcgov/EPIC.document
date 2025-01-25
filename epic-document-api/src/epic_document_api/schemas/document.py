"""Document schema class."""
from marshmallow import EXCLUDE, Schema, fields


class DocumentSchema(Schema):
    """Document schema class."""

    class Meta:
        """Exclude unknown fields in the deserialized output."""

        unknown = EXCLUDE

    id = fields.Int(data_key='id')
    name = fields.Str(data_key='name')
    unique_name = fields.Str(data_key='unique_name')
    path = fields.Str(data_key='path')
