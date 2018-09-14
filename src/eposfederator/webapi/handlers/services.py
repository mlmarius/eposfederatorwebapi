from eposfederator.libs.base.requesthandler import RequestHandler
from eposfederator.webapi.libs import config
from marshmallow_jsonschema import JSONSchema
import logging


class MapHandler(RequestHandler):

    ID = 'api'
    DESCRIPTION = 'Map federator capabilities'
    RESPONSE_TYPE = 'application/json'
    ROUTE = '/services'

    def get(self):
        output = {}
        for plugin_id, plugin in config.APPCONFIG['plugins'].items():
            output[plugin_id] = {}
            for handler in plugin.HANDLERS:
                schema = handler.REQUEST_SCHEMA()
                logging.info(schema)
                logging.info(id(schema))
                output[plugin_id][handler.ID] = {
                    "route": (plugin.BASE_ROUTE + '/' + handler.ROUTE).rstrip('/'),
                    "request_schema": JSONSchema().dump(schema)
                }
        self.write(output)
