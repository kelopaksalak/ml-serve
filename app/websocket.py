from flask_sock import Sock

from app.controllers.ws_controller import register_ws_routes

sock = Sock()


def register_websocket(app):
    sock.init_app(app)
    register_ws_routes(sock)
