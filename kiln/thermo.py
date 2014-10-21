import re
import time
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

class Monitor(threading.Thread):
    def __init__(self, name="3b-000000182b57", callback=None):
        super(Monitor, self).__init__()
        self.daemon = True

        self.device = "/sys/bus/w1/devices/%s/w1_slave"%name
        self.history = deque(maxlen=1048576)
        self.callback = callback

        try:
            from Adafruit_alphanumeric import AlphaScroller
            self.display = AlphaScroller(interval=.4)
            self.display.start()
            self.display.hide()
        except ImportError:
            logger.info("Could not start AlphaScroller")
            self.display = None

        self.running = True
        self.start()

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

    def stop(self):
        self.running = False
        if self.display is not None:
            self.display.stop()

    @property
    def temperature(self):
        return self.history[-1][1]

    def run(self):
        while self.running:
            temp = self._read_temp()
            now = time.time()
            self.history.append(tempsample(now, temp))
            if self.callback is not None:
                self.callback(now, temp)

            if self.display is not None:
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

if __name__ == "__main__":
    mon = Monitor()
    mon.join()
