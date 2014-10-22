import time
import os
import json
import tornado.ioloop
import tornado.web
from tornado import websocket

cwd = os.path.split(os.path.abspath(__file__))[0]

class ClientSocket(websocket.WebSocketHandler):
    def initialize(self, parent):
        self.parent = parent

    def open(self):
        self.parent.sockets.append(self)

    def on_close(self):
        self.parent.sockets.remove(self)

class DataRequest(tornado.web.RequestHandler):
    def initialize(self, manager):
        self.manager = manager

    def get(self):
        data = self.manager.thermocouple.history
        output = [dict(time=ts.time, temp=ts.temp) for ts in data]
        self.write(json.dumps(output))

class DoAction(tornado.web.RequestHandler):
    def initialize(self, manager):
        self.manager = manager

    def get(self, action):
        pass

class WebApp(object):
    def __init__(self, manager, port=8888):
        self.handlers = [
            (r"/ws/", ClientSocket, dict(parent=self)),
            (r"/temperature.json", DataRequest, dict(manager=manager)),
            (r"/do/(.*)", DoAction, dict(manager=manager)),
            (r"/(.*)", tornado.web.StaticFileHandler, dict(path=cwd)),
        ]
        self.sockets = []
        self.port = port

    def send(self, data):
        jsondat = json.dumps(data)
        for sock in self.sockets:
            sock.write_message(jsondat)

    def run(self):
        self.app = tornado.web.Application(self.handlers, gzip=True)
        self.app.listen(8888)
        tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    try:
        import manager
        kiln = manager.Manager()
        app = WebApp(kiln)
        kiln.register(app)
        kiln.start()

        app.run()
    except KeyboardInterrupt:
        kiln.stop()
