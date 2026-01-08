# NinjaTrader 8 Market Replay Batch Downloader (Deep History Miner v2)

## Overview
**v2.05 Update**: Now features "Auto-Hook" technology using direct window automation. No calibration is required.

A robust automation tool designed to "mine" deep historical market replay data for NinjaTrader 8. It automates the tedious process of selecting dates and downloading replay data day-by-day, working backwards from a starting contract.

## Key Features (v2.05)
- **⚡ Auto-Hook Automation**: Directly attaches to the NinjaTrader "Historical Data" window. No manual coordinate calibration needed.
- **🧠 Smart Skipping**: Checks your local drive (`My Documents\NinjaTrader 8\db\replay`) first. If the file exists, it skips the download instantly.
- **🔄 Deep History Cycle**: Automatically switches to previous quarterly contracts (e.g., `MNQ 03-26` -> `MNQ 12-25`) when data runs out.
- **🛡️ Nuclear Popup Killer**: Aggressively detects and dismisses "No Data" popups using active window detection to prevent hanging.
- **⏱️ 5-Minute Safety Timeout**: Hardcoded protection against frozen downloads.

## Requirements
- Windows OS
- NinjaTrader 8 Installed
- Python 3.8+ (if running from source)

## Installation & Running (Source)
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install pywinauto pyautogui pillow
   ```
3. Run the miner:
   ```bash
   python terminal_downloader_v2.py
   ```

## Usage
1. Open **NinjaTrader 8** -> **Tools** -> **Historical Data**.
2. **Expand** the "Get Market Replay Data" panel so the Instrument and Date fields are visible.
3. Run this tool (`NT8 Deep History Miner`).
4. Select your **Starting Contract** (e.g., `MNQ 03-26`) and **Depth** (assignments back).
5. Click **"START MINING"**.
   - *The tool will automatically find the window, type the text, and manage downloads.*

## Building the Executable (.exe)
To create a standalone file for distribution:
```bash
pip install pyinstaller
pyinstaller --noconfirm --onefile --windowed --name "NT8_Replay_Miner_v2.05" --add-data "helper_preview.png;." terminal_downloader_v2.py
```
The executable will appear in the `dist/` folder.

## Disclaimer
This tool uses UI automation. Ensure NinjaTrader is visible while mining is active. Do not minimize the NinjaTrader window (it can be in the background, but must not be minimized to tray).
