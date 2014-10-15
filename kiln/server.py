import time
import tornado.ioloop
import tornado.web

device_file = "/sys/bus/w1/devices/3b-000000182b57/w1_slave"
def read_temp_raw():
	f = open(device_file, 'r')
	lines = f.readlines()
	f.close()
	return lines
 
def read_temp():
	lines = read_temp_raw()
	while lines[0].strip()[-3:] != 'YES':
		time.sleep(0.2)
		lines = read_temp_raw()
	equals_pos = lines[1].find('t=')
	if equals_pos != -1:
		temp_string = lines[1][equals_pos+2:]
		temp_c = float(temp_string) / 1000.0
		temp_f = temp_c * 9.0 / 5.0 + 32.0
		return temp_c, temp_f

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("<!doctype html><head><meta http-equiv='refresh' content='5' ></head><p>Current temperature: %.2f&deg;C, %.2f&deg;F"%read_temp())

application = tornado.web.Application([
    (r"/", MainHandler),
])

if __name__ == "__main__":
    application.listen(8888)
    tornado.ioloop.IOLoop.instance().start()
