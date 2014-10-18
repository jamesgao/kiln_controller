import stepper
import time
import random
import warnings

class KilnController(object):
	def __init__(self, schedule, monitor, interval=5, start_time=None, Kp=.01, Ki=.001, Kd=.001, simulate=True):
		self.schedule = schedule
		self.monitor = monitor
		self.interval = interval
		self.start_time = start_time
		if start_time is None:
			self.start_time = time.time()
		self.regulator = stepper.Regulator(simulate=simulate)
		self.pid = PID(Kp, Ki, Kd)
		self.simulate = simulate
		if simulate:
			self.schedule.insert(0, [0, 15])
		else:
			self.schedule.insert(0, [0, 15])

	@property
	def elapsed(self):
		''' Returns the elapsed time from start in seconds'''
		return time.time() - self.start_time	

	def run(self):
		try:
			self.regulator.ignite()
			print self.elapsed, self.schedule[-1][0]
			while self.elapsed < self.schedule[-1][0]:
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
						print "In epoch %d, elapsed time %f, temperature %f"%(i, ts, setpoint)
						if self.simulate:
							temp = setpoint + random.gauss(-20, 15)
						else:
							temp = self.monitor.temperature

						pid_out = self.pid.update(temp)
						if pid_out < 0: pid_out = 0
						if pid_out > 1: pid_out = 1
						self.regulator.set(pid_out, block=True)

				time.sleep(self.interval - (time.time()-now))
		except:
			import traceback
			traceback.print_exc()

			print "Started at %f"%self.start_time

		self.regulator.off()

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
