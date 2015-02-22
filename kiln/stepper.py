import time
import atexit
import threading
import warnings
import Queue
import logging

logger = logging.getLogger("kiln.Stepper")

try:
    from RPi import GPIO
except ImportError:
    pass

class Stepper(threading.Thread):
    pattern = [
        [1,1,0,0],
        [0,1,1,0],
        [0,0,1,1],
        [1,0,0,1]]

    def __init__(self, pin1=5, pin2=6, pin3=13, pin4=19, timeout=1, home_pin=None):
        super(Stepper, self).__init__()
        self.daemon = True

        self.queue = Queue.Queue()
        self.finished = threading.Event()
        
        self.pins = [pin1, pin2, pin3, pin4]
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin1, GPIO.OUT)
        GPIO.setup(pin2, GPIO.OUT)
        GPIO.setup(pin3, GPIO.OUT)
        GPIO.setup(pin4, GPIO.OUT)
        self.home_pin = home_pin
        GPIO.setup(home_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        self.timeout = timeout
        self.home()
        self.start()

    def stop(self):
        self.queue.put((None, None, None))

    def step(self, num, speed=10, block=False):
        """Step the stepper motor

        Parameters
        ----------
        num : int
            Number of steps
        speed : int
            Number of steps per second
        block : bool
            Block while stepping?
        """
        self.finished.clear()
        self.queue.put((num, speed, block))
        self.finished.wait()

    def home(self):
        if self.home_pin is None:
            raise ValueError("No homing switch defined")

        while GPIO.input(self.home_pin):
            for i in range(len(self.pattern)):
                for pin, out in zip(self.pins, self.pattern[i]):
                    GPIO.output(pin, out)
                time.sleep(1. / 150.)

        self.phase = 0

    def run(self):
        try:
            step, speed, block = self.queue.get()
            while step is not None:
                for pin, out in zip(self.pins, self.pattern[self.phase%len(self.pattern)]):
                    GPIO.output(pin, out)

                if block:
                    self._step(step, speed)
                    self.finished.set()
                else:
                    self.finished.set()
                    self._step_noblock(step, speed)

                try:
                    step, speed, block = self.queue.get(True, self.timeout)
                except Queue.Empty:
                    #handle the timeout, turn off all pins
                    for pin in self.pins:
                        GPIO.output(pin, False)
                    step, speed, block = self.queue.get()
        except:
            import traceback
            traceback.print_exc()

        for pin in self.pins:
            GPIO.output(pin, False)
        GPIO.cleanup()

    def _step_noblock(self, step, speed):
        ispeed = 1. / (2.*speed)
        target = self.phase + step
        while self.phase != target:
            now = time.time()
            self.phase += 1 if target > self.phase else -1
            output = self.pattern[self.phase%len(self.pattern)]
            for pin, out in zip(self.pins, output):
                GPIO.output(pin, out)

            if not self.queue.empty():
                step, speed, block = self.queue.get()
                ispeed = 1. / (2.*speed)
                target += step
                if block:
                    self._step(target - self.phase, speed)
                self.finished.set()

            diff = ispeed - (time.time() - now)
            if (diff) > 0:
                time.sleep(diff) 
            else:
                warnings.warn("Step rate too high, stepping as fast as possible")

    def _step(self, step, speed):
        print "Stepping %d steps at %d steps / second"%(step, speed)
        if step < 0:
            steps = range(step, 0)[::-1]
        else:
            steps = range(step)

        for i in steps:
            now = time.time()
            output = self.pattern[(self.phase+i)%len(self.pattern)]
            for pin, out in zip(self.pins, output):
                GPIO.output(pin, out)

            diff = 1. / (2*speed) - (time.time() - now)
            if (diff) > 0:
                time.sleep(diff)
            
        self.phase += step

class StepperSim(object):
    def __init__(self):
        self.phase = 0

    def step(self, num, speed=10, block=False):
        print "Simulated stepping %d steps at %d steps / second"%(num, speed)
        if block:
            time.sleep(1)

    def stop(self):
        print "stopping simulated regulator"

class Regulator(threading.Thread):
    def __init__(self, maxsteps=4500, minsteps=2480, speed=150, ignite_pin=None, flame_pin=None, simulate=False):
        """Set up a stepper-controlled regulator. Implement some safety measures
        to make sure everything gets shut off at the end

        TODO: integrate flame sensor by converting this into a thread, and checking
        flame state regularly. If flame sensor off, immediately increase gas and attempt
        reignition, or shut off after 5 seconds of failure.

        Parameters
        ----------
        maxsteps : int
            The max value for the regulator, in steps
        minsteps : int
            The minimum position to avoid extinguishing the flame
        speed : int
            Speed to turn the stepper, in steps per second
        ignite_pin : int or None
            If not None, turn on this pin during the ignite sequence
        """

        if simulate:
            self.stepper = StepperSim()
        else:
            self.stepper = Stepper()
            self.stepper.start()

        self.current = 0
        self.max = maxsteps
        self.min = minsteps
        self.speed = speed

        self.ignite_pin = ignite_pin
        if ignite_pin is not None:
            GPIO.setup(ignite_pin, OUT)
        self.flame_pin = flame_pin
        if flame_pin is not None:
            GPIO.setup(flame_pin, IN)
        
        def exit():
            if self.current != 0:
                self.off()
            self.stepper.stop()
        atexit.register(exit)

    def ignite(self, start=2800, delay=1):
        if self.current != 0:
            raise ValueError("Must be off to ignite")

        logger.info("Ignition start")
        self.stepper.step(start, self.speed, block=True)
        if self.ignite_pin is not None:
            GPIO.output(self.ignite_pin, True)
        time.sleep(delay)
        if self.ignite_pin is not None:
            GPIO.output(self.ignite_pin, False)
        self.stepper.step(self.min - start, self.speed, block=True)
        self.current = self.min
        logger.info("Ignition complete")

    def off(self, block=True):
        logger.info("Shutting off gas")
        self.stepper.step(-self.current, self.speed, block=block)
        #self.stepper.home()
        self.current = 0

    def set(self, value, block=False):
        if self.current == 0:
            raise ValueError("System must be ignited to set value")
        if not 0 <= value <= 1:
            raise ValueError("Must give fraction between 0 and 1")
        target = int(value * (self.max - self.min) + self.min)
        nsteps = target - self.current
        print "Currently at %d, target %d, stepping %d"%(self.current, target, nsteps)
        self.current = target
        self.stepper.step(nsteps, self.speed, block=block)

    @property
    def output(self):
        out = (self.current - self.min) / float(self.max - self.min)
        if out < 0:
            return -1
        return out

    def run(self):
        """Check the status of the flame sensor"""
        #since the flame sensor does not yet exist, we'll save this for later
        pass

class Breakout(object):
    def __init__(self, addr, maxsteps=6500, minsteps=((2600, 0), (2300, 15)) ):
        import breakout
        self.device = breakout.Breakout(addr)
        self.min_interp = minsteps
        self.max = maxsteps

        def exit():
            if self.device.motor != 0:
                self.off()
        atexit.register(exit)

    @property
    def min(self):
        temp = self.device.status.aux_temp0
        if temp > self.min_interp[1][1]:
            return self.min_interp[1][0]
        elif temp <= self.min_interp[0][1]:
            return self.min_interp[0][0]
        else:
            mrange = self.min_interp[0][0] - self.min_interp[1][0]
            trange = self.min_interp[1][1] - self.min_interp[0][1]
            mix = (temp - self.min_interp[0][1]) / float(trange)
            return mrange * mix + self.min_interp[1][0]

    def ignite(self, start=2400):
        logger.info("Igniting system")
        self.device.motor = start
        while self.device.motor != start:
            time.sleep(.1)
        self.device.motor = self.min

    @property
    def output(self):
        m = self.min
        out = (self.device.motor - m) / float(self.max - m)
        if out < 0:
            return -1
        return out

    def set(self, value):
        m = self.min
        if self.device.motor == 0:
            raise ValueError('Must ignite first')
        if not 0 <= value <= 1:
            raise ValueError('Must give value between 0 and 1')
        self.device.motor = int((self.max - m)*value + m)

    def off(self):
        self.device.motor = 0
        self.device.ignite = 0
        logger.info("Shutting off regulator")
