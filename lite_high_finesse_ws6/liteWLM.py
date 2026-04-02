"""liteServer for Wavelength Meter WS6-200, served by Windows app"""
# pylint: disable=invalid-name
__version__ = 'v0.2.0 2026-04-01'# Polling added, and some refactoring.

import sys
import time#, os, threading
from math import modf
import argparse
import ctypes

from . import liteserver
print(f'liteWLM {__version__}, liteserver {liteserver.__version__}')

LDO = liteserver.LDO
Device = liteserver.Device
NumberOfInstruments = 2
printv = liteserver.printv

class WLM(Device):
    """Wavelength Meter device, served by Windows app"""
    pargs = None
    def __init__(self, name):
        self.pars = {
          #'wavelength': LDO_WLM('R','Wavelength [nM]',[0.]),
          'cycle':     LDO('R','cycle', 0),
          'frequency': LDO('R','Frequency',0., getter=self.frequency_get, units='THz'),
          'linewidth': LDO('R','Linewidth',0., getter=self.linewidth_get, units='THz'),
          'frequency2': LDO('R','Frequency',0., units='THz'),# getter=self.frequency_get),
          'linewidth2': LDO('R','Linewidth',0., units='THz'),# getter=self.linewidth_get),
          #'sleep':     LDO('W','Sleep time between readings [s]',[1]),
        }
        super().__init__(name, self.pars)

        if not WLM.pargs.simulate:
            printv('>set_dll:')
            self.dll = ctypes.WinDLL('C:\Windows\System32\wlmData.dll')
            #self.dll.GetWavelengthNum.restype = ctypes.c_double
            self.dll.GetFrequencyNum.restype = ctypes.c_double
            self.dll.GetLinewidthNum.restype = ctypes.c_double
            printv('<set_dll:')
        
    def frequency_get(self):
        """Get frequency from WLM, in THz"""
        par = self.pars['frequency']
        if WLM.pargs.simulate:
            par.value = modf(liteserver.time.time())[0]
        else:
            par.value = self.dll.GetFrequencyNum(\
                ctypes.c_long(1), ctypes.c_double(0))
        par.timestamp = liteserver.time.time()
        printv(f'<get f: {par.value}')

    def linewidth_get(self):
        """Get linewidth from WLM, in THz"""
        par = self.pars['linewidth']
        if WLM.pargs.simulate:
            par.value = modf(liteserver.time.time())[0]
        else:
            par.value = self.dll.GetLinewidthNum(\
          ctypes.c_long(1), ctypes.c_double(0))
        par.timestamp = liteserver.time.time()
        printv(f'<get l: {par.value}')

    def poll(self):
        """Poll WLM for new data, update parameters and publish.
        Called by the server in the main loop, after waiting for the polling period."""
        self.pars['cycle'].value[0] += 1
        printv(f"cycle: {self.pars['cycle'].value}")
        ts = time.time()
        self.frequency_get()
        self.linewidth_get()
        for par in self.pars.values():
            par.timestamp = ts
        self.publish()

# parse arguments
parser = argparse.ArgumentParser(description=__doc__
,formatter_class=argparse.ArgumentDefaultsHelpFormatter
,epilog=f'liteWLM: {__version__}')
parser.add_argument('-d','--dbg', action='store_true', help='debugging')
parser.add_argument('-p','--port', type=int, default=9700,
    help='UDP port to listen')
parser.add_argument('-P','--pollingPeriod', type=float, default=10.)
parser.add_argument('-s','--simulate', action='store_true', help='Simulate data')
pargs = parser.parse_args()
WLM.pargs = pargs

try:
    supportedDevices = (WLM('WLM1'),)
except AttributeError:
    print('ERROR: No WinDLL on this machine, try run with --simulate')
    sys.exit(1)

liteserver.Server.Dbg = pargs.dbg
liteserver.ServerDev.PollingInterval = pargs.pollingPeriod
server = liteserver.Server(supportedDevices, port=pargs.port)

server.loop()

