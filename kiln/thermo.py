import time
import re
import threading
import datetime
from collections import deque

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

class Monitor(threading.Thread):
    def __init__(self, name="3b-000000182b57"):
        self.device = "/sys/bus/w1/devices/%s/w1_slave"%name
        self.history = deque(maxlen=1024)

        from Adafruit_alphanumeric import AlphaScroller
        self.display = AlphaScroller(interval=.4)
        self.display.start()
        super(Monitor, self).__init__()
        self.daemon = True

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

    @property
    def temperature(self):
        return self.history[-1][1]

    def run(self):
        while True:
            temp = self._read_temp()
            fahr = temp * 9. / 5. + 32.
            now = datetime.datetime.now()
            self.history.append((now, temp))
            
            text = list('%0.0f'%temp) + ['degree'] + list('C  %0.0f'%fahr)+['degree'] + list("F")

            if 600 <= temp:
                text += [' ', ' ', 'cone']+list("%0.1f"%temp_to_cone(temp))
            text += '    '
            self.display.text = text

if __name__ == "__main__":
    mon = Monitor()
    mon.start()
    mon.join()
