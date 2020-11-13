#!/usr/bin/env python3
# coding=utf-8
# Python access to Elektro Automatik PS 2000 B devices via USB/serial
#
# Supported features:
# - read static device information (manufacturer, serial, device type ...)
# - read dynamic device information (current, voltage)
# - read/write remote control
# - read/write output control
#
# Todo:
# - wrap error results in own telegram
#
# References
# [1] = "PS 2000B Programming Guide" from 2015-05-28
# [2] = "PS 2000B object list"
#

import serial
import struct
import sys
PY_3 = sys.version_info >= (3, 0)


__author__ = "Sören Sprößig <ssproessig@gmail.com>"


def as_string(raw_data):
    """Converts the given raw bytes to a string (removes NULL)"""
    return bytearray(raw_data[:-1])


def as_float(raw_data):
    """Converts the given raw bytes to a float"""
    f = struct.unpack_from(">f", bytearray(raw_data))[0]
    return f


def as_word(raw_data):
    """Converts the given raw bytes to a word"""
    w = struct.unpack_from(">H", bytearray(raw_data))[0]
    return w


def _ord(x):
    """Wrap ord() call as we only need it in Python 2"""
    return x if PY_3 else ord(x)


# noinspection PyClassHasNoInit
class Constants:
    """Communication constants"""
    # communication parameters taken from [1], chapter 2.2
    CONNECTION_BAUD_RATE = 115200
    CONNECTION_PARITY = serial.PARITY_ODD
    CONNECTION_STOP_BITS = 1
    # timeout taken from [1], chapter 3.7
    TIMEOUT_BETWEEN_COMMANDS = 0.05
    # FIXME: for now we only support node=0, meaning first output
    DEVICE_NODE = 0x0
    # according to spec [1] 2.4:
    # maximum length of a telegram is 21 bytes (Byte 0..20)
    MAX_LEN_IN_BYTES = 21


# noinspection PyClassHasNoInit
class Objects:
    """Supported objects ids / commands"""
    DEVICE_TYPE = 0
    DEVICE_SERIAL_NO = 1
    NOMINAL_VOLTAGE = 2
    NOMINAL_CURRENT = 3
    NOMINAL_POWER = 4
    DEVICE_ARTICLE_NO = 6
    MANUFACTURER = 8
    SOFTWARE_VERSION = 9
    SET_VALUE_VOLTAGE = 50
    SET_VALUE_CURRENT = 51
    POWER_SUPPLY_CONTROL = 54
    STATUS_ACTUAL_VALUES = 71


# noinspection PyClassHasNoInit
class ControlParameters:
    """Parameters for controlling the device"""
    SWITCH_MODE_CMD = 0x10
    SWITCH_MODE_REMOTE = 0x10
    SWITCH_MODE_MANUAL = 0x00
    SWITCH_POWER_OUTPUT_CMD = 0x1
    SWITCH_POWER_OUTPUT_ON = 0x1
    SWITCH_POWER_OUTPUT_OFF = 0x0


class Telegram:
    """Base class of a PS2000B telegram - basically allows accessing the raw bytes and does checksum calculation"""

    def __init__(self):
        self._bytes = []
        self._checksum = []
        self.checksum_ok = False

    def _calc_checksum(self):
        cs = 0

        for b in self._bytes:
            cs += b

        cs_high = (cs & 0xff00) >> 8
        cs_low = cs & 0xff

        return [cs_high, cs_low]

    @staticmethod
    def _get_start_delimiter(transmission, expected_data_length):
        result = 0b00000000

        if expected_data_length > 16:
            raise Exception("only 4 bits for expected length can be used")

        result |= (expected_data_length - 1)
        result |= 0b10000
        result |= 0b100000
        result |= transmission << 6
        return result

    def get_byte_array(self):
        return bytearray(self._bytes + self._checksum)


class FromPowerSupply(Telegram):
    """Telegram received from the power supply"""

    def __init__(self, raw_data):
        Telegram.__init__(self)
        data = [_ord(x) for x in raw_data]
        self._bytes = data[0:-2]
        self._checksum = data[len(data) - 2:len(data)]
        self.checksum_ok = self._checksum == self._calc_checksum()

    def get_sd(self):
        return self._bytes[0]

    def get_device_node(self):
        return self._bytes[1]

    def get_object(self):
        return self._bytes[3]

    def get_data(self):
        return self._bytes[3:len(self._bytes)]

    # noinspection PyMethodMayBeStatic
    def get_error(self):
        # FIXME: [1] chapter 3.6 add support for error codes here
        return None


class ToPowerSupply(Telegram):
    """A telegram sent to the power supply"""

    def __init__(self, transmission, data, expected_data_length):
        Telegram.__init__(self)
        self._bytes = []
        self._bytes.append(self._get_start_delimiter(transmission, expected_data_length))
        self._bytes.extend(data)
        self._checksum = self._calc_checksum()
        self.checksum_ok = True


class DeviceInformation:
    """A class carrying all static device information read from the device"""

    def __init__(self):
        self.device_type = ""
        self.device_serial_no = ""
        self.nominal_voltage = 0
        self.nominal_current = 0
        self.nominal_power = 0
        self.manufacturer = ""
        self.device_article_number = ""
        self.software_version = ""

    def __str__(self):
        return "%s %s [%s], SW: %s, Art-Nr: %s, [%0.2f V, %0.2f A, %0.2f W]" % \
               (self.manufacturer,
                self.device_type, self.device_serial_no,
                self.software_version, self.device_article_number,
                self.nominal_voltage, self.nominal_current, self.nominal_power)


class DeviceStatusInformation:
    """A class carrying all dynamic device status information"""

    def __init__(self, raw_data):
        self.remote_control_active = raw_data[0] & 0b1
        self.output_active = raw_data[1] & 0b1
        self.actual_voltage_percent = float(as_word(raw_data[2:4])) / 256
        self.actual_current_percent = float(as_word(raw_data[4:6])) / 256

    def __str__(self):
        return "Remote control active: %s, Output active: %s" % (self.remote_control_active, self.output_active)


class PS2000B:
    """PS 2000 B main communication class"""

    def __init__(self, serial_port):
        self.__device_status_information = None
        self.__serial = serial.Serial(serial_port,
                                      baudrate=Constants.CONNECTION_BAUD_RATE,
                                      timeout=Constants.TIMEOUT_BETWEEN_COMMANDS * 2,
                                      parity=serial.PARITY_ODD,
                                      stopbits=Constants.CONNECTION_STOP_BITS)

        self.__device_information = self.__read_device_information()

    def is_open(self):
        return self.__serial.is_open

    def get_device_information(self):
        return self.__device_information

    def __read_device_information(self):
        result = DeviceInformation()

        # taken from [2]
        result.device_type = as_string(self.__read_device_data(16, Objects.DEVICE_TYPE).get_data())
        result.device_serial_no = as_string(self.__read_device_data(16, Objects.DEVICE_SERIAL_NO).get_data())
        result.nominal_voltage = as_float(self.__read_device_data(4, Objects.NOMINAL_VOLTAGE).get_data())
        result.nominal_current = as_float(self.__read_device_data(4, Objects.NOMINAL_CURRENT).get_data())
        result.nominal_power = as_float(self.__read_device_data(4, Objects.NOMINAL_POWER).get_data())
        result.device_article_number = as_string(self.__read_device_data(16, Objects.DEVICE_ARTICLE_NO).get_data())
        result.manufacturer = as_string(self.__read_device_data(16, Objects.MANUFACTURER).get_data())
        result.software_version = as_string(self.__read_device_data(16, Objects.SOFTWARE_VERSION).get_data())

        return result

    def __read_device_data(self, expected_length, object_id):
        telegram = ToPowerSupply(0b01, [Constants.DEVICE_NODE, object_id], expected_length)
        result = self.__send_and_receive(telegram.get_byte_array())
        return result

    def __send_and_receive(self, raw_bytes):
        self.__serial.write(raw_bytes)
        result = FromPowerSupply(self.__serial.read(Constants.MAX_LEN_IN_BYTES))
        return result

    def get_device_status_information(self):
        """:returns DeviceStatusInformation"""
        if self.__device_status_information is None:
            self.update_device_information()

        return self.__device_status_information

    def update_device_information(self):
        telegram = ToPowerSupply(0b01, [Constants.DEVICE_NODE, Objects.STATUS_ACTUAL_VALUES], 6)
        device_information = self.__send_and_receive(telegram.get_byte_array())
        self.__device_status_information = DeviceStatusInformation(device_information.get_data())

    def __send_device_control(self, p1, p2):
        telegram = ToPowerSupply(0b11, [Constants.DEVICE_NODE, Objects.POWER_SUPPLY_CONTROL, p1, p2], 2)
        _ = self.__send_and_receive(telegram.get_byte_array())
        self.update_device_information()

    def __send_device_data(self, obj, data):
        '''
        Send interger data with obj-id to the PSU
        '''
        telegram = ToPowerSupply(0b11, [Constants.DEVICE_NODE, obj, data >>8, data & 0xff], 4)
        _ = self.__send_and_receive(telegram.get_byte_array())
        self.update_device_information()

    def enable_remote_control(self):
        self.__send_device_control(ControlParameters.SWITCH_MODE_CMD, ControlParameters.SWITCH_MODE_REMOTE)

    def disable_remote_control(self):
        self.__send_device_control(ControlParameters.SWITCH_MODE_CMD, ControlParameters.SWITCH_MODE_MANUAL)

    def enable_output(self):
        self.__send_device_control(ControlParameters.SWITCH_POWER_OUTPUT_CMD, ControlParameters.SWITCH_POWER_OUTPUT_ON)

    def disable_output(self):
        self.__send_device_control(ControlParameters.SWITCH_POWER_OUTPUT_CMD, ControlParameters.SWITCH_POWER_OUTPUT_OFF)

    @property
    def output(self):
        return self.get_device_status_information().output_active

    @output.setter
    def output(self, value):
        if value:
            self.enable_output()
        else:
            self.disable_output()

    def get_voltage(self):
        self.update_device_information()
        voltage = self.__device_information.nominal_voltage * self.__device_status_information.actual_voltage_percent
        return voltage / 100

    def get_voltage_setpoint(self):
        res = self.__read_device_data(2, Objects.SET_VALUE_VOLTAGE).get_data()
        return self.__device_information.nominal_voltage * ((res[0]<<8) + res[1]) / 25600.0

    def set_voltage(self,value):
        self.update_device_information()
        self.enable_remote_control()
        volt = int(round( (value * 25600.0) / self.__device_information.nominal_voltage ))
        self.__send_device_data(Objects.SET_VALUE_VOLTAGE, volt)
        #self.disable_remote_control()

    @property
    def voltage(self):
        return self.get_voltage()

    @voltage.setter
    def voltage(self, value):
        self.set_voltage(value)

    def get_current(self):
        self.update_device_information()
        current = self.__device_information.nominal_current * self.__device_status_information.actual_current_percent
        return current / 100

    def get_curent_setpoint(self):
        res = self.__read_device_data(2, Objects.SET_VALUE_CURRENT).get_data()
        return self.__device_information.nominal_current * ((res[0]<<8) + res[1]) / 25600.0

    def set_current(self, value):
        self.update_device_information()
        self.enable_remote_control()
        curr = int(round( (value * 25600.0) / self.__device_information.nominal_current ))
        self.__send_device_data(Objects.SET_VALUE_CURRENT, curr)
        #self.disable_remote_control()

    @property
    def current(self):
        return self.get_current()

    @current.setter
    def current(self, value):
        self.set_current(value)

