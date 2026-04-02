# lite_high-finesse-ws6

A lightweight network server for the **HighFinesse WS6-200 Wavelength Meter**. It exposes frequency and linewidth readings over UDP using the [liteServer](https://github.com/ASukhanov/liteServer) protocol (CBOR-encoded Lite Data Objects).


## Repository layout

```
lite_high_finesse_ws6/
├── __init__.py
├── liteWLM.py      # WS6-200 device + server entry point
└── liteserver.py   # generic Lite Data Object server
```

## Requirements

- Python 3.8+
- `cbor2`
- For real hardware mode: Windows host with HighFinesse software and `wlmData.dll`
	available at `C:\Windows\System32\wlmData.dll`

Install dependency:

```bash
pip install cbor2
```

## Run

From the repository root:

### Simulation mode (works without hardware)

```bash
python -m lite_high_finesse_ws6.liteWLM --simulate
```

### Hardware mode (Windows + WS6 software)

```bash
python -m lite_high_finesse_ws6.liteWLM
```

## CLI options

| Flag | Default | Description |
|------|---------|-------------|
| `-p`, `--port` | `9700` | UDP server port |
| `-P`, `--pollingPeriod` | `10.0` | Polling period in seconds |
| `-s`, `--simulate` | `False` | Simulate readings (no DLL) |
| `-d`, `--dbg` | `False` | Enable debug logs |

## Exposed device and parameters

Device name: `WLM1`

| Parameter | Access | Units | Meaning |
|-----------|--------|-------|---------|
| `cycle` | R | — | Poll cycle counter |
| `frequency` | R | THz | Channel 1 frequency |
| `linewidth` | R | THz | Channel 1 linewidth |
| `frequency2` | R | THz | Reserved channel 2 frequency field |
| `linewidth2` | R | THz | Reserved channel 2 linewidth field |

## Protocol summary

- Transport: UDP (default port `9700`)
- Encoding: CBOR
- Command set: `info`, `get`, `read`, `set`, `subscribe`, `unsubscribe`

## Version notes

- `liteWLM.py`: `v0.2.0 2026-04-01`
- `liteserver.py`: `3.3.7 2025-08-18`
