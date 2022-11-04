#!/usr/bin/env python3
'''



'''
import sys
import serial, serial.tools.list_ports
import argparse
from pyps2000b import PS2000B

HWID = [0x232E, 0x0010]
VERSION = '0.5'
VERBOSE = 0
ULim = 16
Ilim = 1.4
Uset = 13
Iset = 1


def print_err(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def dprint(debuglevel=1, *args, **kwargs):
    global VERBOSE
    if VERBOSE >= debuglevel:
        print(f'#debug({VERBOSE}): ', *args, **kwargs)

def getPortName(sn=None):
    '''
    Get port name by HWID and optional serial number
    '''
    #serial.tools.list_ports.comports(include_links=False)[0].device
    dprint(1, str('getPortName({}) {}'.format(sn, str([comport.device for comport in serial.tools.list_ports.comports()]))) )
    lPortName = None
    for p in list(serial.tools.list_ports.comports(include_links=False)):
        # if 'USB' in p.hwid:
        if p.vid == HWID[0] and p.pid == HWID[1]:
            if sn == None:
                lPortName = p.device
                break
            else:
                l_psu = PS2000B.PS2000B(p.device)
                if l_psu.get_device_information().device_serial_no.decode() == sn:
                    lPortName = p.device
                    break
    dprint(2, lPortName)
    return lPortName

def findAllPSU():
    '''
    Show all connected PSU found.
    '''
    dprint(1, ('findAllPSU() ', str([comport.device for comport in serial.tools.list_ports.comports()])))
    for p in list(serial.tools.list_ports.comports(include_links=False)):
        if p.vid == HWID[0] and p.pid == HWID[1]:
            l_psu = PS2000B.PS2000B(p.device)
            print(l_psu.get_device_information())

def check_val(par, value):
    '''
    Type-check callback for argparse
    '''
    fvalue = float(value)
    if par == 'u':
        if fvalue < 0 or fvalue >= ULim:
            raise argparse.ArgumentTypeError("%s invalid voltage value" % value)
    elif par =='ovp':
        if fvalue < 0 or fvalue >= 20:
            raise argparse.ArgumentTypeError("%s invalid voltage limit value" % value)
    elif par == 'i':
        if fvalue < 0 or fvalue > Ilim:
            raise argparse.ArgumentTypeError("%s invalid current limit value" % value)
    elif par =='ocp':
        if fvalue < 0 or fvalue >= 10:
            raise argparse.ArgumentTypeError("%s invalid voltage limit value" % value)
    return fvalue

def create_parser():
    '''
    Create parser and arguments
    '''
    parser = argparse.ArgumentParser(description='EA-PS 2042 B Control'+' \n Version: '+VERSION)
    parser.add_argument('-init',action='store_true',help='Initial settings and output off (override with other commands)')
    parser.add_argument('-o', '--output', choices=['on','off'], default='off', help='Activate/deactivate output')
    parser.add_argument('-r', '--remote', choices=['on','off'], default='on', help='Activate/deactivate remote control mode')
    parser.add_argument('-u', type=(lambda x: check_val('u', x)), help='Set output voltage (has to be <U_lim)')
    parser.add_argument('-i', type=lambda x: check_val('i', x), help='Set output current for PSU')
    parser.add_argument('-v', '--verbose', action='count', help='increase output verbosity')
    parser.add_argument('-g', '--get', choices=['voltage','current', 'vlim', 'clim', 'power','output', 'device_info'], default=None, nargs='*', help='Get informations (see README)')
    parser.add_argument('-status',action='store_true',help='Get full status of PSU')
    parser.add_argument('-find',action='store_true',help='Find all connencted PSU')
    parser.add_argument('-sn', type=str, help='Choose device by serial number.')
    parser.add_argument('-p','--port', help='Set serial port. Override port detection.')
    return parser.parse_args()


def main(args):
    global VERBOSE

    if args.verbose:
        VERBOSE = args.verbose
        print(args)
    else:
        VERBOSE = 0

    if args.find:
        findAllPSU()
        sys.exit()

    if args.port == None:
        if args.sn:
            dprint(1,'# use SN=',args.sn)
            portName = getPortName(sn=args.sn)
        else:
            portName = getPortName()
    else:
        portName = args.port

    if portName == None:
        print_err('! EA-PS device not found.')
        sys.exit(1)

    dprint(1, 'Using device at: {}'.format(portName))

    psu = PS2000B.PS2000B(portName)

    if psu.is_open():
        if args.get:
            for arg in args.get:
                if arg == 'voltage':
                    print(psu.voltage)
                elif arg == 'current':
                    print(psu.current)
                elif arg == 'power':
                    print(psu.voltage * psu.current)
                elif arg == 'output':
                    print(psu.output)
                elif arg == 'vlim':
                    print(psu.get_voltage_setpoint())
                elif arg == 'clim':
                    print(psu.get_curent_setpoint())
                # elif arg == 'ovp':
                #     #TODO: implement get_OVP
                # elif arg == 'ocp':
                #     #TODO: implement get_OCP
                elif arg == 'device_info':
                    print('{:<18} {}'.format('Device Type:', psu.get_device_information().device_type.decode()))
                    print('{:<18} {}'.format('Serial no.:', psu.get_device_information().device_serial_no.decode()))
                    print('{:<18} {}'.format('Firmware version:', psu.get_device_information().software_version.decode()))
                else:
                    pass
        else:
            if args.init:
                psu.enable_remote_control()
                psu.output = False
                psu.voltage = Uset
                psu.current = Iset
                # psu.voltage_limit = ULim
                # psu.current_limit = ILim
            else:
                if args.u:
                    psu.voltage = args.u
                # if args.ovp:
                    #TODO: implement set_OVP
                    pass
                # if args.ocp:
                    #TODO: implement set_OCP
                    pass
                if args.i is not None:
                    psu.current = args.i
                if args.output == 'on':
                    psu.output = True
                else:
                    psu.output = False
                if args.remote == 'off':
                    psu.disable_remote_control()
                else:
                    psu.enable_remote_control()

        if args.status:
            print(psu.get_device_status_information())

    else:
        print_err('Error: can not open {}'.format(portName))


if __name__ == '__main__':
    args = create_parser()
    #try:
    main(args)

