"""liteServer for Wavelength Meter WS6-200, served by Windows app.
Requires wlmData.dll from the WLM software, which is a 32-bit DLL and thus 
requires a 32-bit Python installation.
"""
# pylint: disable=invalid-name
__version__ = 'v0.4.1 2026-04-07'# Added pressure and temperature readings.

import sys
import time#, os, threading
from math import modf
import argparse
import ctypes

from . import liteserver
print(f'liteWLM {__version__}, liteserver {liteserver.__version__}')

LDO = liteserver.LDO
Device = liteserver.Device
printv = liteserver.printv
ChannelNumber = 1 # Indicates the signal number (1 to 8) in case of a WLM with
# multi channel switch or with double pulse option (MLC). For WLM's without
# these options 1 should be overhanded

class WLM(Device):
    """Wavelength Meter device, served by Windows app"""
    pargs = None
    def __init__(self, name:str, dll:str):

        print(f'Initializing WLM with dll: {dll}')
        if not WLM.pargs.simulate:
            printv('>set_dll:')
            self.dll = ctypes.WinDLL(dll)
            #self.dll.GetWavelengthNum.restype = ctypes.c_double
            self.dll.GetFrequencyNum.restype = ctypes.c_double
            self.dll.GetLinewidth.restype = ctypes.c_double
            self.dll.GetTemperature.restype = ctypes.c_double
            self.dll.GetPressure.restype = ctypes.c_double
            printv('<set_dll:')

        self.pars = {
          #'wavelength': LDO_WLM('R','Wavelength [nM]',[0.]),
          'cycle':     LDO('RI','cycle', 0),
          'frequency': LDO('R','Frequency',0., getter=self.frequency_get, units='THz'),
          'linewidth': LDO('R','Linewidth',0., units='nm'),
          'temperature': LDO('R','Temperature',0., units='°C'),
          'pressure': LDO('R','Pressure',0., units='mbar'),
          #'dll':       LDO('R','Path to wlmData.dll',dll),
          #'sleep':     LDO('W','Sleep time between readings [s]',[1]),
        }
        super().__init__(name, pars=self.pars)

    def frequency_get(self):
        """Get frequency from WLM, in THz"""
        par = self.PV['frequency']
        if WLM.pargs.simulate:
            par.value = modf(liteserver.time.time())[0]
        else:
            par.value = self.dll.GetFrequencyNum(\
                ctypes.c_long(ChannelNumber), ctypes.c_double(0.))#
            # read others to update the values in the WLM software, otherwise they are not updated
            self.PV['linewidth'].value = self.dll.GetLinewidth(
                #ISSUE: the linewidth is always returned in nm
                ctypes.c_long(ChannelNumber), ctypes.c_double(2.))#cReturnWavelengthAir=1, cReturnWavelengthVacuum=0, cReturnFrequency=2, cReturnEnergy=3
            self.PV['temperature'].value = self.dll.GetTemperature(ctypes.c_double(0))
            self.PV['pressure'].value = self.dll.GetPressure(ctypes.c_double(0))
        par.timestamp = liteserver.time.time()
        printv(f'<get f: {par.value}')

        par.timestamp = liteserver.time.time()
        printv(f'<get l: {par.value}')

    def start(self):
        self.PV['cycle'].value[0] = 0

    def stop(self):
        pass

    def poll(self):
        """Poll WLM for new data, update parameters and publish.
        Called by the server in the main loop, after waiting for the polling period."""
        if self.PV['run'].value[0].startswith('Stop'):
            return 
        self.PV['cycle'].value[0] += 1
        printv(f"cycle: {self.PV['cycle'].value}")
        ts = time.time()
        self.frequency_get()
        for pname in ('frequency','linewidth','temperature','pressure','cycle'):
            par = self.PV[pname]
            #printv(f'{pname}: {par.value} at {par.timestamp}')
            par.timestamp = ts
        self.publish()

# parse arguments
parser = argparse.ArgumentParser(description=__doc__
,formatter_class=argparse.ArgumentDefaultsHelpFormatter
,epilog=f'liteWLM: {__version__}')
parser.add_argument('-d','--dbg', action='store_true', help='debugging')
parser.add_argument('-D','--dll', default = r'C:\Windows\System32\wlmData.dll', help=
    'Path to wlmData.dll file, default is for first instrument')
parser.add_argument('-c','--channel', type=int, default=1, help=
    'Channel number (1 to 8) for WLM with multi-channel switch or double pulse option')
parser.add_argument('-p','--port', type=int, default=9700,
    help='UDP port to listen')
parser.add_argument('-P','--pollingPeriod', type=float, default=10.)
parser.add_argument('-s','--simulate', action='store_true', help='Simulate data')
pargs = parser.parse_args()
WLM.pargs = pargs

try:
    supportedDevices = (WLM('dev1', pargs.dll),)
except AttributeError:
    print('ERROR: No WinDLL on this system, try run with --simulate')
    sys.exit(1)

liteserver.Server.Dbg = pargs.dbg
liteserver.ServerDev.PollingInterval = pargs.pollingPeriod
server = liteserver.Server(supportedDevices, port=pargs.port)

server.loop()
