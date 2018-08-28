import marshmallow


class Schema(marshmallow.Schema):
    class Meta(object):
        strict = True
        dateformat = "%Y-%m-%dT%H:%M:%S"
