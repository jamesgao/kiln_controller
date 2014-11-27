import stepper
import time
import random
import thermo
import threading
import traceback
import logging

import states
import PID

logger = logging.getLogger("kiln.manager")

class Manager(threading.Thread):
	def __init__(self, start=states.Idle, simulate=False):
		"""
		Implement a state machine that cycles through States
		"""
		super(Manager, self).__init__()
		self._send = None

		self.regulator = stepper.Regulator(simulate=simulate)
		if simulate:
			self.therm = thermo.Simulate(regulator=self.regulator)
		else:
			self.therm = thermo.MAX31850()

		self.state = start(self)
		self.state_change = threading.Event()

		self.running = True
		self.start()

	def notify(self, data):
		if self._send is not None:
			self._send(data)
		else:
			logger.info("No notifier set, ignoring message: %s"%data)

	def __getattr__(self, name):
		"""Mutates the manager to return State actions
		If the requested attribute is a function, wrap the function
		such that returned objects which are States indicate a state change
		"""
		attr = getattr(self.state, name)
		if hasattr(attr, "__call__"):
			def func(*args, **kwargs):
				self._change_state(attr(*args, **kwargs))
			return func

		return attr

	def _change_state(self, output):
		if isinstance(output, type) and issubclass(output, states.State) :
			self.state = output(self)
			self.state_change.set()
			self.notify(dict(type="state", state=output.__name__))
		elif isinstance(output, tuple) and issubclass(output[0], states.State):
			newstate, kwargs = output
			self.state = newstate(self, **kwargs)
			self.notify(dict(type="state", state=newstate.__name__))
		elif isinstance(output, dict) and "type" in output:
			self.notify(output)
		elif output is not None:
			logger.warn("Unknown state output: %r"%output)

	def run(self):
		while self.running:
			self._change_state(self.state.run())
	
	def manager_stop(self):
		self.running = False
		self.state_change.set()


class Profile(threading.Thread):
	"""Performs the PID loop required for feedback control"""
	def __init__(self, schedule, therm, regulator, interval=5, start_time=None, callback=None,
			 Kp=.025, Ki=.01, Kd=.005):
		self.schedule = schedule
		self.therm = therm
		self.regulator = regulator
		self.interval = interval
		self.start_time = start_time
		if start_time is None:
			self.start_time = time.time()

		self.pid = PID.PID(Kp, Ki, Kd)
		self.callback = callback
		self.running = True
		self.start()

	@property
	def elapsed(self):
		''' Returns the elapsed time from start in seconds'''
		return time.time() - self.start_time

	@property
	def completed(self):
		return self.elapsed > self.schedule[-1][0]

	def stop(self):
		self.running = False

	def run(self):
		while not self.completed and self.running:
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
					self.regulator.set(pid_out)

					if self.callback is not None:
						self.callback(temp, setpoint, pid_out)

			time.sleep(self.interval - (time.time()-now))
