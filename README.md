# Python-PS2000B
Python library to work with Elektro-Automatik PS 2000 B power supplies via USB.

## Compatibility
Tested with:

+ Python 2.7
+ Python 3.5, 3.6

Tested on:

+ Windows 7 x64
+ Windows 10 x64 Version 1607 (OS Build 14393.2035)
+ Ubuntu 16.04.1 LTS
+ Ubuntu 20.04.1 LTS

## Features of Python-PS2000B
### Supported
- read static device information (manufacturer, serial, device type ...)
- read dynamic device information (current, voltage)
- read/write remote control
- read/write output control

### Still todo
- set voltage and current
- wrap error results in own telegram

## Prerequisites

### Python
The following third-party Python libraries are needed:

* `pyserial` - serial communication library for Python, see https://pypi.python.org/pypi/pyserial

### Windows
On Windows the USB driver (fetch it from http://www.elektroautomatik.de/files/eautomatik/treiber/usb/ea_device_driver.rar) must be installed. Afterwards you can find the serial port `COMxx` in the *device manager*.

### Linux
On Linux the device is detected as `/dev/ttyACMx` (abstract control model, see https://www.rfc1149.net/blog/2013/03/05/what-is-the-difference-between-devttyusbx-and-devttyacmx/). Use `dmesg` after connecting the device to find out `x`.

Most Linuxes will require users to elevate for accessing the device. If you want to access the device as your current user, just add it to the group `dialout` (`ls -lah /dev/ttyACM0` will show you the group to use, usually this is `dialout`) and login again.

## Usage
```python
import time
from pyps2000b import PS2000B


device = PS2000B.PS2000B("/dev/ttyACM0")

print("Device status: %s" % device.get_device_status_information())

device.enable_remote_control()
device.voltage = 5.1
device.current = 1
device.enable_output()

time.sleep(1)

print("Current output: %0.2f V , %0.2f A" % (device.get_voltage(), device.get_current()))

device.output = False
```

## Documentation
+ product website: http://www.elektroautomatik.de/en/ps2000b.html
+ programming guide PS 2000 B: http://www.elektroautomatik.de/files/eautomatik/treiber/ps2000b/programming_ps2000b.zip

