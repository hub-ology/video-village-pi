from __future__ import absolute_import
import serial
import time


DEFAULT_PORT = '/dev/ttyUSB0'

CMD_ACK = '\x03\x14\x00\x00\x00\x14'

ERROR_STATUS_CMD = '\x07\x14\x00\x05\x00\x34\x00\x00\x0C\x0D\x66'

POWER_ON_CMD     = '\x06\x14\x00\x04\x00\x34\x11\x00\x00\x5D'
POWER_OFF_CMD    = '\x06\x14\x00\x04\x00\x34\x11\x01\x00\x5E'
POWER_STATUS_CMD = '\x07\x14\x00\x05\x00\x34\x00\x00\x11\x00\x5E'
POWER_IS_ON_RESPONSE = '\x05\x14\x00\x03\x00\x00\x00\x01\x18'

INPUT_SOURCE_VGA_CMD       = '\x06\x14\x00\x04\x00\x34\x13\x01\x00\x60'
INPUT_SOURCE_VGA2_CMD      = '\x06\x14\x00\x04\x00\x34\x13\x01\x08\x68'
INPUT_SOURCE_HDMI_CMD      = '\x06\x14\x00\x04\x00\x34\x13\x01\x05\x65'
INPUT_SOURCE_COMPOSITE_CMD = '\x06\x14\x00\x04\x00\x34\x13\x01\x05\x65'
INPUT_SOURCE_SVIDEO_CMD    = '\x06\x14\x00\x04\x00\x34\x13\x01\x06\x66'
INPUT_SOURCE_READ_CMD      = '\x07\x14\x00\x05\x00\x34\x00\x00\x13\x01\x61'

RESET_ALL_SETTINGS_CMD   = '\x06\x14\x00\x04\x00\x34\x11\x02\x00\x5F'
RESET_COLOR_SETTINGS_CMD = '\x06\x14\x00\x04\x00\x34\x11\x2A\x00\x87'

LAMP_MODE_NORMAL_CMD   = '\x06\x14\x00\x04\x00\x34\x11\x10\x00\x6D'
LAMP_MODE_ECONOMIC_CMD = '\x06\x14\x00\x04\x00\x34\x11\x10\x01\x6E'
LAMP_MODE_DYNAMIC_CMD  = '\x06\x14\x00\x04\x00\x34\x11\x10\x02\x6F'
LAMP_MODE_SLEEP_CMD    = '\x06\x14\x00\x04\x00\x34\x11\x10\x03\x70'
LAMP_MODE_STATUS_CMD   = '\x07\x14\x00\x05\x00\x34\x00\x00\x11\x10\x6E'

PROJECTOR_POSITION_FRONT_TABLE_CMD = '\x06\x14\x00\x04\x00\x34\x12\x00\x00\x5E'
PROJECTOR_POSITION_REAR_TABLE_CMD = '\x06\x14\x00\x04\x00\x34\x12\x00\x01\x5F'


class Projector(object):

    def __init__(self, port_name=DEFAULT_PORT, baud_rate=115200):
        self.port_name = port_name
        self.baud_rate = baud_rate
        self.serial_port = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

    def connect(self):
        self.serial_port = serial.Serial(port=self.port_name,
                                         baudrate=self.baud_rate,
                                         bytesize=serial.EIGHTBITS,
                                         parity=serial.PARITY_NONE,
                                         stopbits=serial.STOPBITS_ONE,
                                         writeTimeout = 0,
                                         timeout=5,
                                         xonxoff=False,
                                         rtscts=False,
                                         dsrdtr=False)

    def disconnect(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None

    def send(self, command):
        if self.serial_port:
            self.serial_port.write(command)

    def receive(self, byte_count=1):
        """
            Receive data from connected projector
            :return: the data returned by the projector
        """
        if self.serial_port:
            return self.serial_port.read(byte_count)

        return ''

    def flush_input(self):
        if self.serial_port:
            self.serial_port.flushInput()

    def input_source_hdmi(self):
        self.flush_input()
        self.send(INPUT_SOURCE_HDMI_CMD)
        return self.receive(byte_count=6) == CMD_ACK

    def input_source_vga(self):
        self.flush_input()
        self.send(INPUT_SOURCE_VGA_CMD)
        return self.receive(byte_count=6) == CMD_ACK

    def power_on(self):
        self.flush_input()
        self.send(POWER_ON_CMD)
        return self.receive(byte_count=6) == CMD_ACK

    def power_off(self):
        self.flush_input()
        self.send(POWER_OFF_CMD)
        return self.receive(byte_count=6) == CMD_ACK

    def is_on(self):
        self.flush_input()
        self.send(POWER_STATUS_CMD)
        return self.receive(byte_count=9) == POWER_IS_ON_RESPONSE

    def front_table_position(self):
        self.flush_input()
        self.send(PROJECTOR_POSITION_FRONT_TABLE_CMD)
        return self.receive(byte_count=6) == CMD_ACK

    def rear_table_position(self):
        self.flush_input()
        self.send(PROJECTOR_POSITION_REAR_TABLE_CMD)
        return self.receive(byte_count=6) == CMD_ACK

    def reset_settings(self):
        self.flush_input()
        self.send(RESET_ALL_SETTINGS_CMD)
        return self.receive(byte_count=6) == CMD_ACK
