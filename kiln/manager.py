import stepper
import datetime
import numpy as np
import warnings

class KilnController(object):
	""" schedule is of the format:
	[(time1, temp1), (time2, temp2), .... (timen, tempn)]
	where time is in seconds from start of firing and temp is in C"""

	def __init__(self, schedule, monitor, interval=None):
		self.schedule = schedule
		if interval is not None: # interpolate schedule at specified interval size
			temp = np.array(self.schedule)
			temp2 = []
			for i in range(len(self.schedule)-1):
				times = np.arange(self.schedule[i][0], self.schedule[i+1][0], interval)
				temps = np.arange(self.schedule[i][1], self.schedule[i+1][1], interval)
				temp2.extend([(times[j], temps[j]) for j in range(len(times))])
			self.schedule = temp2
		self.start_time = datetime.datetime.now()
		self.setpoint = schedule.pop(0)
		self.monitor = monitor
		self.pid = PID(3.0,0.4,1.2)
		self.regulator = stepper.Regulator()
		self.regulator.start()

	@property
	def elapsed(self):
		''' Returns the elapsed time from start in seconds'''
		return datetime.datetime.now() - self.start_time

	def run(self):
		self.pid.setPoint(self.setpoint[1])
		while self.elapsed<self.setpoint[0]:
			pid_out = self.pid.update(self.monitor.temperature)
			if pid_out<0 or pid_out>1:
				warnings.warn('PID output out of range at ' + str(pid_out) + '!')
			if pid_out < 0: pid_out = 0
			if pid_out > 1: pid_out = 1
			self.regulator.set(pid_out)
		self.setpoint = self.schedule.pop(0)
		if len(schedule)>0:
			self.run()

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
