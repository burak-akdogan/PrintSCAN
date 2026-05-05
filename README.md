# Printer Network Scanner FAST

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A Windows desktop tool that lists locally installed printers, scans the network for printer devices, and lets you manage (delete) printers — all from a simple GUI.

## Features

- List all locally installed Windows printers with IP and floor detection
- Network scanner that finds printers across `192.168.0–7.x` subnets (ports 9100, 631, 515)
- Delete printers directly from the UI
- Copy printer info or just the IP to clipboard via right-click menu
- Ping status shown in the title bar on selection
- Opens Windows Printer Control Panel on double-click
- Runs as Administrator automatically (UAC prompt)

## Requirements

- Windows 10/11
- Python 3.9+
- Dependencies:

```
pip install -r requirements.txt
```

## Run

```
python printer_cleaner.py
```

## Build (standalone EXE)

```
pyinstaller --onefile --windowed --uac-admin printer_cleaner.py
```


> **Note:** An `--icon=printer.ico` flag can be added if you supply a `.ico` file.

## Notes

- Admin privileges are required to delete printers.
- The network scan checks 2032 IP addresses concurrently (80 threads). Adjust `max_workers` in the source if needed.
- Floor detection (`1st`, `2nd`, `3rd`) is based on keywords in the printer name.

## License

This project is licensed under the [MIT License](LICENSE).
