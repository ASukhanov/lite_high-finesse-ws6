"""liteServer for Wavelength Meter WS6-200, served by Windows app.
Support several instruments by providing a comma-separated list of wlmData.dll 
files for each instrument, and the channel number (1 to 8) for WLM 
with multi-channel switch or double pulse option.
Requires wlmData.dll from the WLM software, which is a 32-bit DLL and thus 
requires a 32-bit Python installation.
"""
# pylint: disable=invalid-name
__version__ = 'v0.3.0 2026-04-06'# pargs.dll is now an argument, linewidth is now in THz

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
            self.dll.GetLinewidthNum.restype = ctypes.c_double
            printv('<set_dll:')

        self.pars = {
          #'wavelength': LDO_WLM('R','Wavelength [nM]',[0.]),
          'cycle':     LDO('RI','cycle', 0),
          'frequency': LDO('R','Frequency',0., getter=self.frequency_get, units='THz'),
          'linewidth': LDO('R','Linewidth',0., getter=self.linewidth_get, units='THz'),
          'dll':       LDO('R','Path to wlmData.dll',dll),
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
                ctypes.c_long(ChannelNumber), ctypes.c_double(0))#
        par.timestamp = liteserver.time.time()
        printv(f'<get f: {par.value}')

    def linewidth_get(self):
        """Get linewidth from WLM, in THz"""
        par = self.PV['linewidth']
        if WLM.pargs.simulate:
            par.value = modf(liteserver.time.time())[0]
        else:
            par.value = self.dll.GetLinewidthNum(
          #ctypes.c_long(2), ctypes.c_double(0))# see wlmConst.py for cReturnFrequency=2
          ctypes.c_long(1), ctypes.c_double(0))# cReturnWavelengthAir=1, cReturnWavelengthVacuum=0, cReturnFrequency=2, cReturnEnergy=3

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
        self.linewidth_get()
        for pname in ('frequency', 'linewidth','cycle'):
            par = self.PV[pname]
            printv(f'{pname}: {par.value} at {par.timestamp}')
            par.timestamp = ts
        self.publish()

# parse arguments
parser = argparse.ArgumentParser(description=__doc__
,formatter_class=argparse.ArgumentDefaultsHelpFormatter
,epilog=f'liteWLM: {__version__}')
parser.add_argument('-d','--dbg', action='store_true', help='debugging')
parser.add_argument('-D','--dlls', default = 'C:/Windows/System32/wlmData.dll', help=
    'Comma-separated list of wlmData.dll files for each instrument, default is for first instrument')
parser.add_argument('-c','--channel', type=int, default=1, help=
    'Channel number (1 to 8) for WLM with multi-channel switch or double pulse option')
parser.add_argument('-p','--port', type=int, default=9700,
    help='UDP port to listen')
parser.add_argument('-P','--pollingPeriod', type=float, default=10.)
parser.add_argument('-s','--simulate', action='store_true', help='Simulate data')
pargs = parser.parse_args()
WLM.pargs = pargs

supportedDevices = []
for i,dllFile in enumerate(pargs.dlls.split(',')):
    try:
        supportedDevices.append(WLM(f'dev{i+1}', dllFile))
    except AttributeError:
        print(f'ERROR: No WinDLL for WLM {i+1}, try run with --simulate')

if len(supportedDevices) == 0:
    sys.exit(1)

liteserver.Server.Dbg = pargs.dbg
liteserver.ServerDev.PollingInterval = pargs.pollingPeriod
server = liteserver.Server(supportedDevices, port=pargs.port)

server.loop()

