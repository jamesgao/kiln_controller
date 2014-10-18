import time
import atexit
import threading
import warnings
import Queue

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

    def __init__(self, pin1=5, pin2=6, pin3=13, pin4=19, timeout=5):
        self.queue = Queue.Queue()
        self.finished = threading.Event()
        
        self.pins = [pin1, pin2, pin3, pin4]
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(pin1, GPIO.OUT)
        GPIO.setup(pin2, GPIO.OUT)
        GPIO.setup(pin3, GPIO.OUT)
        GPIO.setup(pin4, GPIO.OUT)

        self.phase = 0
        self.timeout = timeout
        super(Stepper, self).__init__()
        self.daemon = True

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
        print "stopping"


class Regulator(object):
    def __init__(self, maxsteps=4500, minsteps=2400, speed=150, ignite_pin=None, simulate=False):
        """Set up a stepper-controlled regulator. Implement some safety measures
        to make sure everything gets shut off at the end

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
        
        def exit():
            if self.current != 0:
                self.off()
            self.stepper.stop()
        atexit.register(exit)

    def ignite(self, start=2800, delay=1):
        print "Ignition..."
        self.stepper.step(start, self.speed, block=True)
        if self.ignite_pin is not None:
            GPIO.output(self.ignite_pin, True)
        time.sleep(delay)
        if self.ignite_pin is not None:
            GPIO.output(self.ignite_pin, False)
        self.stepper.step(self.min - start, self.speed)
        self.current = self.min
        print "Done!"

    def off(self, block=True):
        print "Turning off..."
        self.stepper.step(-self.current, self.speed, block=block)
        self.current = 0
        print "Done!"

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
