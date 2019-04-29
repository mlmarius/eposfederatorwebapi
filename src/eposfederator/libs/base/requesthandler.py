import tornado
import logging
import tornado.web
from urllib.request import urlopen
from urllib.request import Request
import re


class TokenValidation():
    # token validation: should match "Bearer <token>"
    def token_validation(token):
        resp = None
        # fixed length token (43 chars)
        if token is not None and re.match("Bearer [a-zA-Z0-9_-]{43}$", token):
            resp = token
        return resp


class RequestHandler(tornado.web.RequestHandler):
    def prepare(self):
        # auth-service (or whatever): google, facebook, edugain, ...
        # auth_service = self.request.headers.get('auth-service', None)
        # try to get the OAUTH token
        btoken = self.request.headers.get('Authorization', None)  # "Bearer <token>"
        if TokenValidation.token_validation(btoken) is not None:
            # now validate token
            auth_url = "https://aaai.epos-eu.org/oauth2/userinfo"
            # set header : "Authorization: Bearer <token>"
            authreq = Request(auth_url, headers={"Authorization": btoken})
            authresp = urlopen(authreq)
            
            token_valid = False
            if authresp.getcode() == 200:
                token_valid = True
            
            # read userinfo for accounting
            # {sub, lastname, firstname, eduPersonUniqueId, email}
            # user_obj = authresp.read()

            if token_valid is False:
                raise tornado.web.HTTPError(401)

        else:
            fridge_authorization = self.request.headers.get('Fridge-Authorize', None)
            if fridge_authorization != "FDerkaeriASFLK":
                raise tornado.web.HTTPError(403)

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
