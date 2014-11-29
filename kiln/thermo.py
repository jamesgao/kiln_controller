import re
import time
import random
import datetime
import logging
import threading
from collections import deque, namedtuple

logger = logging.getLogger("thermo")

def temp_to_cone(temp):
    """Convert the current temperature to cone value using linear interpolation"""
    cones = [600,614,635,683,717,747,792,804,838,852,884,894,900,923,955,984,999,1046,1060,1101,1120,1137,1154,1162,1168,1186,1196,1222,1240,1263,1280,1305,1315,1326,1346]
    names = [str(i).replace('-', '0') for i in range(-22,0)] + [str(i) for i in range(1, 14)]
    for i in range(len(cones)-1):
        low, high = cones[i], cones[i+1]
        if low <= temp < high:
            frac = (temp - low) / float(high - low)
            return names[i]+'.%d'%int(frac*10)
    return "13+"

tempsample = namedtuple("tempsample", ['time', 'temp'])

class MAX31850(object):
    def __init__(self, name="3b-000000182b57", smooth_window=4):
        self.device = "/sys/bus/w1/devices/%s/w1_slave"%name
        self.history = deque(maxlen=smooth_window)
        self.last = None

    def _read_temp(self):
        with open(self.device, 'r') as f:
            lines = f.readlines()

        while lines[0].strip()[-3:] != 'YES':
            time.sleep(0.2)
            with open(self.device, 'r') as f:
                lines = f.readlines()

        match = re.match(r'^[0-9a-f\s]{27}t=(\d+)$', lines[1])
        if match is not None:
            return float(match.group(1)) / 1000.0

    def get(self):
        """Blocking call to retrieve latest temperature sample"""
        self.history.append(self._read_temp())
        self.last = time.time()
        return self.temperature

    @property
    def temperature(self):
        if self.last is None or time.time() - self.last > 5:
            return self.get()

        return tempsample(self.last, sum(self.history) / float(len(self.history)))

class Simulate(object):
    def __init__(self, regulator, smooth_window=8):
        self.regulator = regulator
        self.history = deque(maxlen=smooth_window)
        self.last = None

    def _read_temp(self):
        time.sleep(.25)
        return max([self.regulator.output, 0]) * 1000. + 15+random.gauss(0,.2)

    def get(self):
        self.history.append(self._read_temp())
        self.last = time.time()
        return self.temperature

    @property
    def temperature(self):
        if self.last is None or time.time() - self.last > 5:
            return self.get()

        return tempsample(self.last, sum(self.history) / float(len(self.history)))

class Breakout(object):
    def __init__(self, addr):
        import breakout
        self.device = breakout.Breakout(addr)

    def get(self):
        time.sleep(.25)
        return tempsample(time.time(), self.device.temperature)

    @property
    def temperature(self):
        return self.device.temperature

class Monitor(threading.Thread):
    def __init__(self, cls=MAX31850, **kwargs):
        self.therm = cls(**kwargs)
        self.running = True
        
        from Adafruit_alphanumeric import AlphaScroller
        self.display = AlphaScroller(interval=.4)
        self.display.start()
        self.display.hide()

    def run(self):
        while self.running:
            _, temp = self.therm.get()

            if temp > 50:
                if not self.display.shown:
                    self.display.show()
                fahr = temp * 9. / 5. + 32.
                text = list('%0.0f'%temp) + ['degree'] + list('C  %0.0f'%fahr)+['degree'] + list("F")
                if 600 <= temp:
                    text += [' ', ' ', 'cone']+list(temp_to_cone(temp))
                self.display.set_text(text, reset=False)
            elif self.display.shown:
                self.display.hide()

    def stop(self):
        self.running = False
        self.display.stop()


if __name__ == "__main__":
    monitor = Monitor()
    monitor.start()
