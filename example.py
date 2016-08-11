import platform
import time

from pyps2000b import PS2000B


DEVICE = "COM10" if platform.system() == "Windows" else "/dev/ttyACM0"

# connection to the device is automatically opened
print("Connecting to device at %s..." % DEVICE)
device = PS2000B.PS2000B(DEVICE)

# static device information can be read
print("Connection open: %s" % device.is_open())
print("Device: %s" % device.get_device_information())

# dynamic device status information can be read
device_status_info = device.get_device_status_information()
print("Device status: %s" % device_status_info)
print("Current output: %0.2f V , %0.2f A" % (device.get_voltage(), device.get_current()))

# device can be controlled
if not device_status_info.remote_control_active:
    print("...will enable remote control...")
    device.enable_remote_control()

print("...now enabling the power output control...")
device.enable_output()
print("Device status: %s" % device.get_device_status_information())
time.sleep(1)
print("Current output: %0.2f V , %0.2f A" % (device.get_voltage(), device.get_current()))
print("...after 2 seconds power output will be disabled again ...")
time.sleep(2)
device.disable_output()
print("...and disabling remote control again.")
device.disable_remote_control()

print("Device status: %s" % device.get_device_status_information())

# FIXME  add support to set output current and voltage
