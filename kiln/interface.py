import smbus
import struct
from collections import namedtuple

Status = namedtuple('Status', 'ignite flame motor main_temp weight aux_temp0 aux_temp1')

class Kiln(object):
    fmt = struct.Struct('<2BI4f')
    def __init__(self, addr, bus=1):
        self.bus = smbus.SMBus(1)
        self.addr = addr

    @property
    def status(self):
        chars = map(chr, self.bus.read_i2c_block_data(self.addr, 0, self.fmt.size))
        return Status._make(self.fmt.unpack(''.join(chars)))

    def __repr__(self):
        return repr(self.status)

    @property
    def motor(self):
        return self.status.motor
    
    @motor.setter
    def motor(self, pos):
        out = map(ord, struct.pack('I',pos))
        self.bus.write_i2c_block_data(self.addr,ord('M'), out) 
    
    @property
    def temperature(self):
        data = self.bus.read_i2c_block_data(self.addr,ord('T'), 4)
        return struct.unpack('<f', ''.join(map(chr, data)))[0]
    
    @property
    def ignite(self):
        return self.status.ignite
    
    @ignite.setter
    def ignite(self, output):
        self.bus.write_i2c_block_data(self.addr,ord('I'), [int(output)])
