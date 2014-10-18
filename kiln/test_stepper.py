import time
import stepper

def test_noblock():
	reg = stepper.Regulator(ignite_pin=None)

	reg.ignite()
	reg.set(.5)
	time.sleep(.5)
	reg.set(.1)
	time.sleep(.5)
	reg.set(.5, block=True)
	return reg
