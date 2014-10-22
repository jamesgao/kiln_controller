"""Based on the pattern provided here:
http://python-3-patterns-idioms-test.readthedocs.org/en/latest/StateMachine.html
"""
import time
import traceback
import manager
from collections import deque

class State(object):
	def __init__(self, machine):
		self.parent = machine

	def run(self):
		"""Action that must be continuously run while in this state"""
		self.parent.state_change.clear()
		self.parent.state_change.wait()

class Idle(State):
	def __init__(self, parent):
		super(Idle, self).__init__(parent)
		self.history = deque(maxlen=1024) #about 10 minutes worth

	def run(self):
		ts = self.parent.therm.get()
		self.history.append(ts)
		self.parent.notify(dict(type="temperature", time=ts.time, temp=ts.temp))

	def ignite(self):
		_ignite(self.parent.regulator, self.parent.notify)
		return Lit, dict(history=self.history)

	def start(self, **kwargs):
		_ignite(self.parent.regulator, self.parent.notify)
		kwargs['history'] = deque(self.history)
		return Running, kwargs

class Lit(State):
	def __init__(self, parent, history):
		super(Lit, self).__init__(parent)
		self.history = deque(history)

	def set(self, value):
		try:
			self.parent.regulator.set(value)
			self.parent.notify(dict(type="success"))
		except:
			self.parent.notify(dict(type="error", msg=traceback.format_exc()))

	def run(self):
		ts = self.parent.therm.get()
		self.history.append(ts)

	def start(self, **kwargs):
		kwargs['history'] = self.history
		return Running, kwargs

	def stop(self):
		_shutoff(self.parent.regulator, self.parent.notify)
		return Idle

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

class Running(State):
	def __init__(self, parent, history, **kwargs):
		super(Running, self).__init__(parent)
		self.profile = manager.Profile(therm=self.parent.therm, regulator=self.parent.regulator, 
			callback=self._notify, **kwargs)
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

		self.history.append(self.parent.therm.get())

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