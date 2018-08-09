from eposfederator.libs.base.requesthandler import RequestHandler
from eposfederator.webapi.libs import config
from marshmallow_jsonschema import JSONSchema
import logging


class MapHandler(RequestHandler):

    ID = 'api'
    DESCRIPTION = 'Says hello'
    RESPONSE_TYPE = 'application/json'
    ROUTE = '/services'

    def get(self):
        output = {}

        json_schema = JSONSchema()

        for plugin_id, plugin in config.APPCONFIG['plugins'].items():
            output[plugin_id] = {}
            logging.info(plugin.HANDLERS)
            for handler in plugin.HANDLERS:
                schema = handler.REQUEST_SCHEMA()
                output[plugin_id][handler.ID] = {
                    "route": plugin.BASE_ROUTE + handler.ROUTE,
                    "request_schema": json_schema.dump(schema)
                }
        logging.info(config.APPCONFIG)
        self.write(output)
        # self.write("hello")
