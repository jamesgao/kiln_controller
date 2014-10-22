import stepper
import time
import random
import thermo
import warnings
import threading
import traceback
import logging
import states

logger = logging.getLogger("kiln.manager")

class Manager(threading.Thread):
	def __init__(self, start=states.Idle):
		"""
		Implement a state machine that cycles through States
		"""
		super(Manager, self).__init__()
		self._send = None
		self.thermocouple = thermo.Monitor(self._send_state)
		self.regulator = stepper.Regulator()

		self.profile = None

		self.state = start(self)
		self.state_change = threading.Event()

		self.running = True
		self.start()

	def register(self, webapp):
		self._send = webapp.send

	def notify(self, data):
		if self._send is not None:
			self._send(data)
		else:
			logging.warn("No notifier set, ignoring message: %s"%data)

	def _send_state(self, time, temp):
		profile = None
		if self.profile is not None:
			profile.get_state()

		state = dict(
			output=self.regulator.output,
			profile=profile,
			time=time,
			temp=temp,
		)
		if self._send is not None:
			self._send(state)

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
		if isinstance(output, states.State) :
			self.state = output()
			self.state_change.set()
			self.notify(dict(type="change", state=newstate.__name__))
		elif isinstance(output, tuple) and isinstance(output[0], states.State):
			newstate, kwargs = output
			self.state = output(**kwargs)
			self.notify(dict(type="change", state=newstate.__name__))
		elif isinstance(output, dict) and "type" in dict:
			self.notify(output)
		elif output is not None:
			logger.warn("Unknown state output: %s"%output)

	def run(self):
		while running:
			self._change_state(self.state.run())
	
	def stop(self):
		self.running = False
		self.state_change.set()