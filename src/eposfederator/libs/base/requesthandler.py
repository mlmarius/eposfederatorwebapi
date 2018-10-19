import tornado
import logging


class RequestHandler(tornado.web.RequestHandler):

    def prepare(self):
        logging.info("Response type should be {}".format(self.RESPONSE_TYPE))
        self.set_header('Content-Type', self.RESPONSE_TYPE)

    def write_error(self, status_code, **kwargs):
        """Write errors as JSON."""
        self.set_header('Content-Type', 'application/json')
        if 'exc_info' in kwargs:
            etype, value, traceback = kwargs['exc_info']
            if hasattr(value, 'messages'):
                self.write({'errors': value.messages})
                self.finish()
