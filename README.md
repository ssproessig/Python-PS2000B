# Python-PS2000B
Python library to work with Elektro-Automatik PS 2000 B power supplies via USB.

## Compatibility
Tested with:

+ Python 2.7 

Tested on:

+ Windows 7 x64 


## Prerequisites

### Python
The following third-party Python libraries are needed:

* pyserial - serial communication library for Python, see https://pypi.python.org/pypi/pyserial

### Windows
On Windows the USB driver (fetch it from http://www.elektroautomatik.de/files/eautomatik/treiber/usb/ea_device_driver.rar) must be installed. Afterwards you can find the serial port `COMxx` in the *device manager*.

### Linux
On Linux the device is detected as `/dev/ttyACMx` (abstract control model, see https://www.rfc1149.net/blog/2013/03/05/what-is-the-difference-between-devttyusbx-and-devttyacmx/). Use `dmesg` after connecting the device to find out `x`.

Most Linuxes will require users to elevate for accessing the device. If you want to access the device as your current user, just add it to the group `dialout` (`ls -lah /dev/ttyACM0` will show you the group to use, usually this is `dialout`) and login again.

## Usage
TODO

## Documentation
+ product website: http://www.elektroautomatik.de/en/ps2000b.html
+ programming guide PS 2000 B: http://www.elektroautomatik.de/files/eautomatik/treiber/ps2000b/programming_ps2000b.zip

