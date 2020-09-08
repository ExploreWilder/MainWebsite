#
# Copyright 2018-2020 Clement
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its contributors
#    may be used to endorse or promote products derived from this software
#    without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from .utils import *

try:
    from .secret_config import Production_config, Config, Testing_config
except ImportError:
    from .config import Production_config, Config, Testing_config

from .cache import cache

def create_app(is_testing=False):
    """ Create and configure an instance of the Flask application. """
    from .social_networks import social_networks_app, share_link
    from .visitor_space import visitor_app
    from .admin_space import admin_app
    from .map import map_app
    from .kofi import kofi_app

    app = Flask(__name__)

    @app.template_filter("numerator")
    def numerator(s):
        return fracstr_to_numerator(s)

    @app.template_filter("denominator")
    def denominator(s):
        return fracstr_to_denominator(s)

    is_debug = app.config["DEBUG"]
    app.config.from_object(Config if is_debug else Production_config)
    if is_debug:
        logging.basicConfig(level=logging.DEBUG)
    if is_testing:
        app.config.from_object(Testing_config)
    app.config["STATIC_PACKAGE"] = get_static_package_config()
    
    @app.context_processor
    def app_ctx_processor():
        return dict(
            share_link=share_link,
            allowed_external_connections=allowed_external_connections)
    
    if not is_debug and not is_testing:
        sentry_sdk.init(
            dsn=app.config["SENTRY_DSN"],
            integrations=[FlaskIntegration()])

    app.config["CSP_NONCE"] = csp_nonce()
    talisman = Talisman(
        app,
        content_security_policy=app.config["CSP_CONFIG"],
        content_security_policy_nonce_in=app.config["CSP_NONCE_IN"])

    Markdown(app, extensions=app.config["MD_EXT"])
    csrf = SeaSurf(app) # validation will be active for all POST requests if not testing

    # register the database commands
    from . import db
    db.init_app(app)

    @app.route("/error")
    @app.errorhandler(403)
    @app.errorhandler(404) # "page not found" or access forbidden
    @app.errorhandler(405) # "method not allowed"
    def just_error(error):
        """
        The 404-error page with the specific HTTP field set.
        Any catched error are considered 404 to make guesses harder.
        """
        return render_template(
            "error.html",
            is_prod=not app.config["DEBUG"]), 404
    
    @app.errorhandler(500)
    def handle_500(e):
        """
        More information:
        https://docs.sentry.io/enriching-error-data/user-feedback/?platform=flask
        https://flask.palletsprojects.com/en/1.1.x/errorhandling/#unhandled-exceptions
        """
        return render_template(
            "internal_server_error.html",
            sentry_event_id=sentry_sdk.last_event_id(),
            is_prod=not app.config["DEBUG"]), 500

    # apply the blueprints to the app
    cache.init_app(app)
    app.register_blueprint(social_networks_app, url_prefix="/social_networks")
    app.register_blueprint(visitor_app)
    app.register_blueprint(admin_app, url_prefix="/admin")
    app.register_blueprint(map_app, url_prefix="/map")
    app.register_blueprint(kofi_app, url_prefix="/kofi")
    csrf.exempt_urls("/kofi/webhook")

    return app
