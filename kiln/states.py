"""Based on the pattern provided here:
http://python-3-patterns-idioms-test.readthedocs.org/en/latest/StateMachine.html
"""
import traceback

class State(object):
	def __init__(self, machine):
		self.parent = machine

	def run(self):
		"""Action that must be continuously run while in this state"""
		pass

class Idle(State):
	def ignite(self):
		_ignite(self.parent.regulator, self.parent.notify)
		return Lit,

	def start(self):
		_ignite(self.parent.regulator, self.parent.notify)
		return Running,

class Lit(State):
	def set(self, value):
		try:
			self.parent.regulator.set(value)
			self.parent.notify(dict(type="success"))
		except:
			self.parent.notify(dict(type="error", msg=traceback.format_exc()))

	def start(self, schedule, interval=5, start_time=None):
		return Running, dict(schedule=schedule, interval=interval, start_time=start_time)

	def stop(self):
		_shutoff(self.parent.regulator, self.parent.notify)
		return Idle,


class Running(State):
	@property
	def elapsed(self):
		''' Returns the elapsed time from start in seconds'''
		return time.time() - self.start_time	

	def run(self):
		now = time.time()
		ts = self.elapsed
		#find epoch
		for i in range(len(self.schedule)-1):
			if self.schedule[i][0] < ts < self.schedule[i+1][0]:
				time0, temp0 = self.schedule[i]
				time1, temp1 = self.schedule[i+1]
				frac = (ts - time0) / (time1 - time0)
				setpoint = frac * (temp1 - temp0) + temp0
				self.pid.setPoint(setpoint)

				temp = self.monitor.temperature
				pid_out = self.pid.update(temp)
				if pid_out < 0: pid_out = 0
				if pid_out > 1: pid_out = 1
				self.regulator.set(pid_out, block=True)

		if ts > self.schedule[-1][0]:
			_shutoff(self.parent.regulator, self.parent.notify)
			return Idle,

		time.sleep(self.interval - (time.time()-now))

	def pause(self):
		return Lit,

	def stop(self):
		_shutoff(self.parent.regulator, self.parent.notify)
		return Idle,


def _ignite(regulator, notify):
	try:
		regulator.ignite()
		msg = dict(type="success")
	except ValueError:
		msg = dict(type="error", msg="Cannot ignite: regulator not off")
	except Exception as e:
		msg = dict(type="error", msg=traceback.format_exc())
	notify(msg)

def _shutoff(regulator, notify):
	try:
		regulator.off()
		msg = dict(type="success")
	except ValueError:
		msg = dict(type="error", msg="Cannot shutoff: regulator not lit")
	except Exception as e:
		msg = dict(type="error", msg=traceback.format_exc())
	notify(msg)