import stepper
import time
import random
import thermo
import warnings
import threading
import traceback

class Manager(threading.Thread):
	def __init__(self):
		"""
		Create a Manager instance that manages the electronics for the kiln.
		Fundamentally, this just means that four components need to be connected:

		The thermocouple, the regulator stepper, and PID controller, and the webserver
		"""
		self._send = None
		self.monitor = thermo.Monitor(self._send_state)
		self.regulator = stepper.Regulator(self._regulator_error)

		self.profile = None

	def register(self, webapp):
		self._send = webapp.send

	def _send_state(self, time, temp):
		profile = None
		if self.profile is not None:
			profile.get_state()

		state = dict(
			output=self.regulator.output
			profile=profile,
			time=time,
			temp=temp,
		)
		if self._send is not None:
			self._send(state)

	def _regulator_error(self, msg):
		if self._send is not None:
			self._send(dict())



class Profile(object):
	def __init__(self, schedule, monitor, regulator, interval=5, start_time=None, Kp=.025, Ki=.01, Kd=.005):
		self.schedule = schedule
		self.monitor = monitor
		self.interval = interval
		self.start_time = start_time
		if start_time is None:
			self.start_time = time.time()
		self.regulator = regulator
		self.pid = PID(Kp, Ki, Kd)
		self.running = True

	def get_state(self):
		state = dict(
			start_time=self.start_time,
			elapsed=self.elapsed,
		)
		return state

	def stop(self):
		self.running = False

class PID(object):
	"""
	Discrete PID control
	#The recipe gives simple implementation of a Discrete Proportional-Integral-Derivative (PID) controller. PID controller gives output value for error between desired reference input and measurement feedback to minimize error value.
	#More information: http://en.wikipedia.org/wiki/PID_controller
	#
	#cnr437@gmail.com
	#
	#######	Example	#########
	#
	#p=PID(3.0,0.4,1.2)
	#p.setPoint(5.0)
	#while True:
	#     pid = p.update(measurement_value)
	#
	#
	"""

	def __init__(self, P=2.0, I=0.0, D=1.0, Derivator=0, Integrator=0, Integrator_max=500, Integrator_min=-500):

		self.Kp=P
		self.Ki=I
		self.Kd=D
		self.Derivator=Derivator
		self.Integrator=Integrator
		self.Integrator_max=Integrator_max
		self.Integrator_min=Integrator_min

		self.set_point=0.0
		self.error=0.0

	def update(self,current_value):
		"""
		Calculate PID output value for given reference input and feedback
		"""

		self.error = self.set_point - current_value

		self.P_value = self.Kp * self.error
		self.D_value = self.Kd * ( self.error - self.Derivator)
		self.Derivator = self.error

		self.Integrator = self.Integrator + self.error

		if self.Integrator > self.Integrator_max:
			self.Integrator = self.Integrator_max
		elif self.Integrator < self.Integrator_min:
			self.Integrator = self.Integrator_min

		self.I_value = self.Integrator * self.Ki
		PID = self.P_value + self.I_value + self.D_value

		print "PID: %f, %f, %f: %f"%(self.P_value, self.I_value, self.D_value, PID)

		return PID

	def setPoint(self,set_point):
		"""
		Initilize the setpoint of PID
		"""
		self.set_point = set_point
		self.Integrator=0
		self.Derivator=0

	def setIntegrator(self, Integrator):
		self.Integrator = Integrator

	def setDerivator(self, Derivator):
		self.Derivator = Derivator

	def setKp(self,P):
		self.Kp=P

	def setKi(self,I):
		self.Ki=I

	def setKd(self,D):
		self.Kd=D

	def getPoint(self):
		return self.set_point

	def getError(self):
		return self.error

	def getIntegrator(self):
		return self.Integrator

	def getDerivator(self):
		return self.Derivator
