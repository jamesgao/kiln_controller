import smbus
import struct
from collections import namedtuple

Status = namedtuple('Status', 'ignite flame motor main_temp ambient weight aux_temp0 aux_temp1')

class Breakout(object):
    fmt = struct.Struct('<BBH5f')
    def __init__(self, addr, bus=1):
        self.bus = smbus.SMBus(1)
        self.addr = addr

    @property
    def status(self):
        while True:
            try:
                chars = map(chr, self.bus.read_i2c_block_data(self.addr, 0, self.fmt.size))
                return Status._make(self.fmt.unpack(''.join(chars)))
            except IOError:
                #ignore IOError due to i2c timeout
                pass

    def __repr__(self):
        return repr(self.status)

    def _get_cmd(self, cmd, fmt='f'):
        s = struct.Struct('<'+fmt)
        while True:
            try:
                data = self.bus.read_i2c_block_data(self.addr, ord(cmd), s.size)
                return s.unpack(''.join(map(chr, data)))[0]
            except IOError:
                #ignore IOError due to i2c timeout
                pass

    def _set_cmd(self, cmd, value, fmt='f'):
        out = map(ord, struct.pack('<'+fmt, value))
        self.bus.write_i2c_block_data(self.addr, ord(cmd), out)

    @property
    def motor(self):
        return self._get_cmd('M', fmt='H')
    
    @motor.setter
    def motor(self, pos):
        self._set_cmd('M', pos, fmt='H')
    
    @property
    def temperature(self):
        return self._get_cmd('T', fmt='f')
    
    @property
    def ignite(self):
        return self._get_cmd('I', fmt='B')
    
    @ignite.setter
    def ignite(self, output):
        self._set_cmd('I', output, fmt='B')
