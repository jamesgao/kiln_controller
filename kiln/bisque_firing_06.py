import manager
import thermo
import sys

if __name__ == "__main__":
	start_time = None
	if len(sys.argv) > 1:
		start_time = float(sys.argv[1])
	schedule = [[2*60*60, 176], [4*60*60, 620], [6*60*60, 1013], [6*60*60+20*60, 1013]]
	mon = thermo.Monitor()
	mon.start()
	#schedule = [[20, 176], [40, 620], [60, 1013]]
	kiln = manager.KilnController(schedule, mon, start_time=start_time, simulate=False)
	kiln.run()