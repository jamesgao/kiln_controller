#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import time
import json
import traceback
import inspect

import tornado.ioloop
import tornado.web
from tornado import websocket

import paths

cone_symbol = re.compile(r'\^([0-9]{1,3})')

class ClientSocket(websocket.WebSocketHandler):
    def initialize(self, parent):
        self.parent = parent

    def open(self):
        self.parent.clients.append(self)

    def on_close(self):
        self.parent.clients.remove(self)

class ManagerHandler(tornado.web.RequestHandler):
    def initialize(self, manager):
        self.manager = manager

class MainHandler(ManagerHandler):
    def get(self):
        files = os.listdir(paths.profile_path)
        fixname = lambda x: cone_symbol.sub(r'Δ\1', os.path.splitext(x)[0].replace("_", " "))
        profiles = dict((fname, fixname(fname)) for fname in files)
        return self.render(os.path.join(paths.html_templates, "main.html"), 
            state=self.manager.state.__class__.__name__,
            profiles=profiles,
        )

class DataRequest(ManagerHandler):
    def get(self):
        data = list(self.manager.history)
        output = [dict(time=ts.time, temp=ts.temp) for ts in data]
        self.write(json.dumps(output))

class ProfileHandler(tornado.web.RequestHandler):
    def get(self, name):
        try:
            with open(os.path.join(paths.profile_path, name)) as fp:
                self.write(fp.read())
        except IOError:
            self.write_error(404)

    def post(self, name):
        try:
            schedule = self.get_argument("schedule")
            fname = os.path.join(paths.profile_path, name)
            with open(fname, 'w') as fp:
                json.dump(schedule, fp)
            self.write(dict(type="success"))
        except IOError:
            self.write_error(404)
        except Exception as e:
            self.write(dict(type="error", error=repr(e), msg=traceback.format_exc()))

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
            (r"^/$", MainHandler, dict(manager=manager)),
            (r"^/ws/?$", ClientSocket, dict(parent=self)),
            (r"^/temperature.json$", DataRequest, dict(manager=manager)),
            (r"^/do/(.*)/?$", DoAction, dict(manager=manager)),
            (r"^/profile/?(.*)$", ProfileHandler),
            (r"^/(.*)$", tornado.web.StaticFileHandler, dict(path=paths.html_static)),
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
