# NinjaTrader 8 Market Replay Batch Downloader (Deep History Miner)

## Overview
A robust automation tool designed to "mine" deep historical market replay data for NinjaTrader 8. It automates the tedious process of selecting dates and downloading replay data day-by-day, working backwards from a starting contract.

## Features
- **Deep History Mining:** Works backwards day-by-day from a start date.
- **Auto-Contract Chaining:** Automatically switches to previous quarterly assignments (e.g., `MNQ 03-26` -> `MNQ 12-25`) when data runs out.
- **Stop Loss Mechanism:** Automatically stops or switches contracts after `X` consecutive days of no data.
- **3-Point Calibration:** Ensures reliable automation by locking coordinates for Instrument Field, Date Field, and Download Button.
- **Background & Overlay UI:** Step-by-step instructions.

## Requirements
- Windows OS
- NinjaTrader 8 Installed
- Python 3.8+

## Installation
1. Clone this repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Open **NinjaTrader 8** -> **Tools** -> **Historical Data** -> **Market Replay**.
2. Run the miner:
   ```bash
   python terminal_downloader.py
   ```
3. Click **"HOVER OVER DOWNLOAD BUTTON"** and following the calibration steps in the log.
4. Select your contract and settings (e.g., Deep History, Stop after 5 misses).
5. Click **"START MINING"**.
6. When the popup appears, click OK and **immediately click the Instrument Text Field** in NinjaTrader to give it focus.

## Disclaimer
This tool uses UI automation (`pyautogui`). Ensure NinjaTrader is visible and do not use the mouse/keyboard while mining is active.
