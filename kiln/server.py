import time
import tornado.ioloop
import tornado.web


class MainHandler(tornado.web.RequestHandler):
    def initialize(self, monitor):
        self.monitor = monitor
    def get(self):
        self.write("<!doctype html><head><meta http-equiv='refresh' content='5' ></head><p>Current temperature: %.2f&deg;C, %.2f&deg;F"%read_temp())

if __name__ == "__main__":
    
    application = tornado.web.Application([
        (r"/", MainHandler, dict(monitor=mon)),
    ])

    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
