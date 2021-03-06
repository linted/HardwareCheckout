import os
import json
from datetime import datetime, timedelta

from tornado.web import Application, RequestHandler, StaticFileHandler
from tornado_sqlalchemy import SQLAlchemy


from .config import db_path
from .main import main as main_blueprint
from .auth import auth as auth_blueprint
from .terminals import terms as terminal_blueprint
from .queue import queue as queue_blueprint
from .device import device as device_blueprint
from .admin import admin as admin_blueprint
from .models import db


class NotFoundHandler(RequestHandler):
    def get(self) -> None:
        self.set_status(404)
        self.render("error.html", error="404")


def create_redirect() -> Application:
    class sslRedirect(RequestHandler):
        def get(self) -> None:
            self.redirect("https://" + self.request.host, permanent=True)

        def post(self) -> None:
            self.redirect("https://" + self.request.host, permanent=True)

    app = Application([(r"/.*", sslRedirect)])
    return app


def create_app() -> Application:
    app = Application(
        [
            *(main_blueprint.publish("/")),
            *(auth_blueprint.publish("/")),
            *(terminal_blueprint.publish("/")),
            *(queue_blueprint.publish("/queue")),
            *(device_blueprint.publish("/device")),
            *(admin_blueprint.publish("/admin")),
        ],
        login_url="/login",
        cookie_secret=os.environ.get(
            "TORNADO_SECRET_KEY",
            open(
                os.path.join(
                    os.path.dirname(os.path.realpath(__file__)), "../cookie.key"
                ),
                "r",
            ).read(),
        ),
        template_path="HardwareCheckout/templates/",
        static_path="HardwareCheckout/static/",
        db=db,
        # xsrf_cookies=True,  #TODO
        websocket_ping_interval=10000,
        websocket_ping_timeout=30000,
        default_handler_class=NotFoundHandler,
    )

    return app
