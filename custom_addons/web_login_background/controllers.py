from odoo import http
from odoo.http import request

from odoo.addons.auth_signup.controllers.main import AuthSignupHome
from odoo.addons.web.controllers.home import Home
import logging
_logger = logging.getLogger(__name__)

class Background(Home):
    
    @http.route('/web/login', type='http', auth='none', readonly=False)
    def web_login(self, redirect=None, **kw):
        picture_url = request.env["ir.attachment"].get_background_pic()
        response = super().web_login(redirect=redirect, **kw)
        if hasattr(response, "qcontext"):
            response.qcontext["picture_url"] = picture_url

        return response


class BackgroundSignup(AuthSignupHome):
    @http.route("/web/signup", type="http", auth="public")
    def web_auth_signup(self, *args, **kw):
        picture_url = request.env["ir.attachment"].get_background_pic()
        response = super().web_auth_signup(*args, **kw)
        if hasattr(response, "qcontext"):
            response.qcontext["picture_url"] = picture_url

        return response
