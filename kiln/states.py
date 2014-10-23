"""Based on the pattern provided here:
http://python-3-patterns-idioms-test.readthedocs.org/en/latest/StateMachine.html
"""
import time
import traceback
import manager
from collections import deque

class State(object):
	def __init__(self, manager):
		self.parent = manager

	def run(self):
		"""Action that must be continuously run while in this state"""
		ts = self.parent.therm.get()
		self.history.append(ts)
		return dict(type="temperature", time=ts.time, temp=ts.temp, output=self.parent.regulator.output)

class Idle(State):
	def __init__(self, manager):
		super(Idle, self).__init__(manager)
		self.history = deque(maxlen=1024) #about 10 minutes worth

	def ignite(self):
		_ignite(self.parent.regulator, self.parent.notify)
		return Lit, dict(history=self.history)

	def start(self, schedule, start_time=None, interval=5):
		_ignite(self.parent.regulator, self.parent.notify)
		kwargs = dict(history=self.history, 
			schedule=json.loads(schedule), 
			start_time=float(start_time), 
			interval=float(interval)
		)
		return Running, kwargs

class Lit(State):
	def __init__(self, parent, history):
		super(Lit, self).__init__(parent)
		self.history = deque(history)

	def set(self, value):
		try:
			self.parent.regulator.set(float(value))
			return dict(type="success")
		except:
			return dict(type="error", msg=traceback.format_exc())

	def start(self, schedule, start_time=None, interval=5):
		kwargs = dict(history=self.history, 
			schedule=json.loads(schedule), 
			start_time=float(start_time), 
			interval=float(interval)
		)
		return Running, kwargs
	def stop(self):
		_shutoff(self.parent.regulator, self.parent.notify)
		return Cooling, dict(history=self.history)

class Cooling(State):
	def __init__(self, parent, history):
		super(Cooling, self).__init__(parent)
		self.history = history

	def run(self):
		ts = self.parent.therm.get()
		self.history.append(ts)
		if ts.temp < 50:
			#TODO: save temperature log somewhere
			return Idle
		return dict(type="temperature", time=ts.time, temp=ts.temp)

	def ignite(self):
		_ignite(self.parent.regulator, self.parent.notify)
		return Lit, dict(history=self.history)

	def start(self, schedule, start_time=None, interval=5):
		_ignite(self.parent.regulator, self.parent.notify)
		kwargs = dict(history=self.history, 
			schedule=json.loads(schedule), 
			start_time=float(start_time), 
			interval=float(interval)
		)
		return Running, kwargs

class Running(State):
	def __init__(self, parent, history, start_time=None, **kwargs):
		super(Running, self).__init__(parent)
		self.start_time = start_time
		self.profile = manager.Profile(therm=self.parent.therm, regulator=self.parent.regulator, 
			callback=self._notify, start_time=start_time **kwargs)
		self.history = history

	def _notify(self, therm, setpoint, out):
		self.parent.notify(dict(
			type="profile",
			temp=therm,
			setpoint=setpoint,
			output=out,
			ts=self.profile.elapsed,
		))

	def run(self):
		if self.profile.completed:
			self.parent.notify(dict(type="profile",status="complete"))
			_shutoff(self.parent.regulator, self.parent.notify)
			return Cooling, dict(history=self.history)

		return super(Running, self).run()

	def pause(self):
		self.profile.stop()
		return Lit, dict(history=self.history)

	def stop(self):
		self.profile.stop()
		_shutoff(self.parent.regulator, self.parent.notify)
		return Cooling, dict(history=self.history)


def _ignite(regulator, notify):
	try:
		regulator.ignite()
		msg = dict(type="success")
	except ValueError:
		msg = dict(type="error", msg="Cannot ignite: regulator not off")
	except Exception as e:
		msg = dict(type="error", error=repr(e), msg=traceback.format_exc())
	notify(msg)

def _shutoff(regulator, notify):
	try:
		regulator.off()
		msg = dict(type="success")
	except ValueError:
		msg = dict(type="error", msg="Cannot shutoff: regulator not lit")
	except Exception as e:
		msg = dict(type="error", error=repr(e), msg=traceback.format_exc())
	notify(msg)