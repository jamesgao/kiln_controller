import time
import os
import json
import traceback
import inspect

import tornado.ioloop
import tornado.web
from tornado import websocket

cwd = os.path.split(os.path.abspath(__file__))[0]

class ManagerHandler(tornado.web.RequestHandler):
    def initialize(self, manager):
        self.manager = manager

class MainHandler(ManagerHandler):
    def get(self):
        return self.render("template.html", state=self.manager.state.__class__.__name__)

class ClientSocket(websocket.WebSocketHandler):
    def initialize(self, parent):
        self.parent = parent

    def open(self):
        self.parent.clients.append(self)

    def on_close(self):
        self.parent.clients.remove(self)

class DataRequest(ManagerHandler):
    def get(self):
        data = list(self.manager.history)
        output = [dict(time=ts.time, temp=ts.temp) for ts in data]
        self.write(json.dumps(output))

class DoAction(ManagerHandler):
    def _run(self, name, argfunc):
        func = getattr(self.manager.state, name)
        #Introspect the function, get the arguments
        args, varargs, keywords, defaults = inspect.getargspec(func)
        
        kwargs = dict()
        if defaults is not None:
            #keyword arguments
            for arg, d in zip(args[-len(defaults):], defaults):
                kwargs[arg] = argfunc(arg, default=d)
            end = len(defaults)
        else:
            end = len(args)

        #required arguments
        for arg in args[1:end]:
            kwargs[arg] = argfunc(arg)

        realfunc = getattr(self.manager, name)
        realfunc(**kwargs)

    def get(self, action):
        try:
            self._run(action, self.get_query_argument)
            self.write(json.dumps(dict(type="success")))
        except Exception as e:
            self.write(json.dumps(dict(type="error", error=repr(e), msg=traceback.format_exc())))

    def post(self, action):
        try:
            self._run(action, self.get_argument)
            self.write(json.dumps(dict(type="success")))
        except Exception as e:
            self.write(json.dumps(dict(type="error", error=repr(e), msg=traceback.format_exc())))        

class WebApp(object):
    def __init__(self, manager, port=8888):
        self.handlers = [
            (r'/', MainHandler, dict(manager=manager)),
            (r"/ws/", ClientSocket, dict(parent=self)),
            (r"/temperature.json", DataRequest, dict(manager=manager)),
            (r"/do/(.*)", DoAction, dict(manager=manager)),
            (r"/(.*)", tornado.web.StaticFileHandler, dict(path=cwd)),
        ]
        self.clients = []
        self.port = port

    def send(self, data):
        jsondat = json.dumps(data)
        for sock in self.clients:
            sock.write_message(jsondat)

    def run(self):
        self.app = tornado.web.Application(self.handlers, gzip=True)
        self.app.listen(8888)
        tornado.ioloop.IOLoop.instance().start()

if __name__ == "__main__":
    try:
        import manager
        kiln = manager.Manager(simulate=True)
        app = WebApp(kiln)
        kiln._send = app.send

        app.run()
    except KeyboardInterrupt:
        kiln.manager_stop()
