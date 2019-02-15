import tornado
import logging
import tornado.web


class RequestHandler(tornado.web.RequestHandler):

    def prepare(self):

        # try to get the OAUTH token
        token = self.get_argument("token", None)
        # TODO: validate token with regular expression! What does the token look like ?!?
        if token is not None:
            # now validate token
            token_valid = True

            if token_valid is False:
                raise tornado.web.HTTPError(404)

        else:
            fridge_authorization = self.request.headers.get('Fridge-Authorize', None)
            if fridge_authorization != "FDerkaeriASFLK":
                raise tornado.web.HTTPError(404)

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
