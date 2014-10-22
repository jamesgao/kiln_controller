"""Based on the pattern provided here:
http://python-3-patterns-idioms-test.readthedocs.org/en/latest/StateMachine.html
"""
import time
import traceback
import PID

class State(object):
	def __init__(self, machine):
		self.parent = machine

	def run(self):
		"""Action that must be continuously run while in this state"""
		self.parent.state_change.clear()
		self.parent.state_change.wait()

class Idle(State):
	def ignite(self):
		_ignite(self.parent.regulator, self.parent.notify)
		return Lit

	def start(self, **kwargs):
		_ignite(self.parent.regulator, self.parent.notify)
		return Running, kwargs

class Lit(State):
	def set(self, value):
		try:
			self.parent.regulator.set(value)
			self.parent.notify(dict(type="success"))
		except:
			self.parent.notify(dict(type="error", msg=traceback.format_exc()))

	def start(self, **kwargs):
		return Running, kwargs

	def stop(self):
		_shutoff(self.parent.regulator, self.parent.notify)
		return Idle

class Running(State):
	def __init__(self, parent, schedule, interval=5, start_time=None, Kp=.025, Ki=.01, Kd=.005):
		self.schedule = schedule
		self.thermocouple = parent.thermocouple
		self.interval = interval
		self.start_time = start_time
		if start_time is None:
			self.start_time = time.time()
		self.regulator = parent.regulator
		self.pid = PID.PID(Kp, Ki, Kd)
		self.running = True
		super(Running, self).__init__(parent)

	@property
	def elapsed(self):
		''' Returns the elapsed time from start in seconds'''
		return time.time() - self.start_time

	@property
	def _info(self):
		return dict(type="profile", 
			output=pid_out, 
			start_time=self.start_time,
			elapsed=self.elapsed,
		)

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

				temp = self.thermocouple.temperature
				pid_out = self.pid.update(temp)
				if pid_out < 0: pid_out = 0
				if pid_out > 1: pid_out = 1
				self.regulator.set(pid_out, block=True)
				self.parent.notify(self.info)

		if ts > self.schedule[-1][0]:
			self.parent.notify(dict(type="profile",status="complete"))
			_shutoff(self.parent.regulator, self.parent.notify)
			return Idle,

		time.sleep(self.interval - (time.time()-now))

	def pause(self):
		return Lit

	def stop(self):
		_shutoff(self.parent.regulator, self.parent.notify)
		return Idle


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