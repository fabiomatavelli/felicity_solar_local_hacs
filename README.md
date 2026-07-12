# 🔋 Felicity Solar Local for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg?style=for-the-badge)](https://github.com/hacs/integration)
[![Tests](https://github.com/fabiomatavelli/felicity_solar_local_hacs/actions/workflows/test.yml/badge.svg)](https://github.com/fabiomatavelli/felicity_solar_local_hacs/actions/workflows/test.yml)

A Home Assistant custom integration that reads Felicity Solar battery data **directly over
your local network** - no cloud account, no internet dependency. It talks to the battery's
onboard WiFi module using its local TCP/JSON protocol.

> Looking for the cloud-based integration instead (Shine/FSolar account, inverters + batteries)?
> See [`felicity_solar_hacs`](https://github.com/matheustavarestrindade/felicity_solar_hacs).

## ✨ Features

- **Local polling, no cloud**: connects straight to the battery's IP over TCP.
- **UI configuration**: add a battery by IP, no YAML required.
- **All battery data**: voltage, current, power, SOC, SOH, capacity, all 16 individual cell
  voltages, min/max cell voltage, temperatures, charge/discharge limits, fault/warning codes.
- **Nothing hidden**: a diagnostic "Raw data" sensor exposes the complete device payload as
  attributes, even fields not mapped to a dedicated sensor.
- **Multi-model aware**: sensor field mapping is looked up per battery model (see
  [Battery model support](#-battery-model-support) below) instead of hardcoded to one model.

## 🛠️ Installation

### Method 1: HACS (Recommended)

1. Open Home Assistant and go to **HACS**.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Add this repository's URL, category **Integration**.
4. Find **Felicity Solar Local** in HACS and click **Download**.
5. **Restart Home Assistant**.

### Method 2: Manual

1. Download the latest release from this repository.
2. Copy the `custom_components/felicity_solar_local` folder into your Home Assistant
   `/config/custom_components/` directory.
3. **Restart Home Assistant**.

## ⚙️ Configuration

1. Find your battery's local IP address (check your router's DHCP leases).
2. In Home Assistant, go to **Settings** > **Devices & Services** > **+ Add Integration**.
3. Search for **Felicity Solar Local**.
4. Enter the battery's IP address (port defaults to `53970`).
5. Repeat for each additional battery - one config entry per battery/IP.

Update interval (default 30s, minimum 10s) can be changed afterwards from the integration's
**Configure** button.

### Confirming your battery works before setting up the integration

Run the standalone probe script against your battery's IP to confirm it speaks the protocol
and see its raw data:

```console
python3 scripts/probe.py <battery-ip>
```

## 🔋 Battery model support

This integration was built and verified against a **Felicity Solar FLB48314TG1-H**
(`Type=112, SubType=7353`). Field names/scaling were cross-checked live against the same
battery's readings from Felicity's cloud API - see `custom_components/felicity_solar_local/profiles.py`
for the full mapping.

Other Felicity WiFi-battery models likely speak the same protocol (same command, port, and
JSON shape were originally reverse-engineered against a different model, the FLA48300), but
scaling/field meaning for models other than the FLB48314TG1-H is **not verified**. Unrecognized
models fall back to a best-effort generic profile with the same field names, and the raw data
sensor always shows the untouched payload regardless.

**Have a different Felicity Solar WiFi battery?** Run `scripts/probe.py` against it, compare
the output to `tests/fixtures/sample_response.json`, and open a PR adding a new
`BatteryProfile` to `profiles.py` (see [CONTRIBUTING.md](CONTRIBUTING.md)) - matched by your
device's own `Type`/`SubType` codes so it doesn't affect other models.

## 📡 Protocol

Reverse-engineered from [`mxbode/Felicitysolar-FLA48300-WiFi-Readout`](https://github.com/mxbode/Felicitysolar-FLA48300-WiFi-Readout)
(credit to that project for documenting the command/port). That repository has no license and
is written in JavaScript; this integration is a fresh Python implementation based on the
observed protocol facts, not a port of its code. In short: plain TCP on port `53970`, send
`wifilocalMonitor:get dev real infor`, read the JSON reply up to its first `}`, then write a
single `.` byte back as an acknowledgement.

## 👨‍💻 Author

Created and maintained by **Fábio Matavelli** ([@fabiomatavelli](https://github.com/fabiomatavelli)).

Contributions welcome - see [CONTRIBUTING.md](CONTRIBUTING.md).
