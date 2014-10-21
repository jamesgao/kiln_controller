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
    def initialize(self, monitor):
        self.monitor = monitor

    def get(self):
        data = self.monitor.history
        output = [dict(time=ts[0], temp=ts[1]) for ts in ]
        self.write(json.dumps(output))

class DoAction(tornado.web.RequestHandler):
    def initialize(self, controller):
        self.controller = controller

    def get(self, action):
        pass

class WebApp(object):
    def __init__(self, monitor, port=8888):
        self.handlers = [
            (r"/ws/", ClientSocket, dict(parent=self)),
            (r"/data.json", DataRequest, dict(monitor=monitor)),
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
        import thermo
        monitor = thermo.Monitor()

        app = WebApp(monitor)
        def send_temp(time, temp):
            app.send(dict(time=time, temp=temp))
        monitor.callback = send_temp
        monitor.start()
        app.run()
    except KeyboardInterrupt:
        monitor.stop()
