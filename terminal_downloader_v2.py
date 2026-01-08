import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import timedelta, date
import os
import re
from contract_utils import get_active_trading_period, get_previous_contract, get_contract_expiry
from PIL import Image, ImageTk 

# pywinauto imports
from pywinauto import Desktop
from pywinauto.findwindows import ElementNotFoundError

import pyautogui # Added back for robust popup handling

import ctypes

# Professional Trading Terminal Color Scheme (Kept from V1)
VERSION = "2.05"

COLORS = {
    'bg_dark': '#0a1612',
    'bg_medium': '#0d2117',
    'bg_panel': '#162d22',
    'accent_green': '#00ff41',
    'accent_gold': '#ffd700',
    'text_primary': '#e0ffe0',
    'text_secondary': '#80c080',
    'text_muted': '#506850',
    'success': '#00ff41',
    'warning': '#ffb900',
    'danger': '#ff4444',
    'button_bg': '#1e4d2b',
    'button_active': '#00ff41',
}

class TradingTerminalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"NT8 MARKET REPLAY MINER v{VERSION} (AUTO-HOOK)")
        self.root.geometry("1150x1000")
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Custom style
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Terminal.TCombobox', 
                       fieldbackground=COLORS['bg_panel'],
                       background=COLORS['bg_panel'],
                       foreground=COLORS['text_primary'],
                       arrowcolor=COLORS['accent_green'])
        
        self.existing_dates = set()
        
        # === HEADER ===
        header = tk.Frame(root, bg=COLORS['bg_medium'], height=60)
        header.pack(fill="x", padx=0, pady=0)
        
        title = tk.Label(header, text=f"⚡ NT8 DEEP HISTORY MINER v{VERSION}",
                        font=("Consolas", 18, "bold"),
                        bg=COLORS['bg_medium'],
                        fg=COLORS['accent_green'])
        title.pack(pady=15)
        # === INSTRUCTIONS CANVAS (Top) ===
        canvas_height = 200 
        self.instr_canvas = tk.Canvas(root, bg=COLORS['bg_panel'], height=canvas_height, highlightthickness=0)
        self.instr_canvas.pack(fill="x", padx=10, pady=(10, 5))
        
        self.photo = None
        try:
            img_path = "helper_preview.png"
            if os.path.exists(img_path):
                raw_img = Image.open(img_path)
                target_width = 1080
                w_percent = (target_width / float(raw_img.size[0]))
                h_size = int((float(raw_img.size[1]) * float(w_percent)))
                if h_size > canvas_height:
                    self.instr_canvas.config(height=h_size)
                    canvas_height = h_size
                raw_img = raw_img.resize((target_width, h_size), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(raw_img)
                self.instr_canvas.create_image(0, 0, image=self.photo, anchor="nw")
        except Exception as e:
            print(f"Could not load image: {e}")

        # Instruction Text
        instruction_lines = [
            "Instructions:",
            "1. Open NinjaTrader 8 -> Tools -> Historical Data",
            "2. Ensure the 'Get Market Replay Data' panel is OPEN",
            "3. Select Start Contract & Configuration below",
            "4. Click START MINING"
        ]
        
        text_center_x = 550
        text_start_y = 20
        line_height = 25
        
        for i, line in enumerate(instruction_lines):
            y = text_start_y + (i * line_height)
            if i == 0:
                font_spec = ("Consolas", 12, "bold")
                color = COLORS['accent_gold']
            else:
                font_spec = ("Consolas", 9, "bold")
                color = "white"
                
            self.instr_canvas.create_text(text_center_x + 1, y + 1, text=line, anchor="center", font=font_spec, fill="black")
            self.instr_canvas.create_text(text_center_x, y, text=line, anchor="center", font=font_spec, fill=color)

        # === MAIN CONTAINER ===
        main_container = tk.Frame(root, bg=COLORS['bg_dark'])
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === LEFT PANEL: Configuration ===
        left_panel = tk.Frame(main_container, bg=COLORS['bg_panel'], width=500)
        left_panel.pack(side="left", fill="both", padx=(0, 5), pady=0)
        
        config_title = tk.Label(left_panel, text="CONFIGURATION", font=("Consolas", 11, "bold"), bg=COLORS['bg_panel'], fg=COLORS['accent_gold'], anchor="w")
        config_title.pack(fill="x", padx=15, pady=(15, 10))
        
        grid_frame = tk.Frame(left_panel, bg=COLORS['bg_panel'])
        grid_frame.pack(fill="x", padx=15, pady=5)
        grid_frame.columnconfigure(0, weight=1)
        grid_frame.columnconfigure(1, weight=2)

        # Contracts
        tk.Label(grid_frame, text="Starting Contract:", font=("Consolas", 9, "bold"), bg=COLORS['bg_panel'], fg=COLORS['text_secondary'], anchor="e").grid(row=0, column=0, sticky="e", padx=5, pady=8)
        contracts = self._get_contracts()
        self.inst_combo = ttk.Combobox(grid_frame, values=contracts, width=18, font=("Consolas", 10), style='Terminal.TCombobox')
        self.inst_combo.set("MNQ 03-26")
        self.inst_combo.grid(row=0, column=1, sticky="w", padx=5, pady=8)
        
        # Mode
        tk.Label(grid_frame, text="Mining Mode:", font=("Consolas", 9, "bold"), bg=COLORS['bg_panel'], fg=COLORS['text_secondary'], anchor="e").grid(row=1, column=0, sticky="e", padx=5, pady=8)
        mode_frame = tk.Frame(grid_frame, bg=COLORS['bg_panel'])
        mode_frame.grid(row=1, column=1, sticky="w", padx=5, pady=8)
        self.mining_mode = tk.StringVar(value="deep")
        tk.Radiobutton(mode_frame, text="Deep History", variable=self.mining_mode, value="deep", font=("Consolas", 9), bg=COLORS['bg_panel'], fg=COLORS['text_primary'], selectcolor=COLORS['bg_dark'], activebackground=COLORS['bg_panel'], activeforeground=COLORS['accent_green']).pack(side="left")
        tk.Radiobutton(mode_frame, text="Single Contract", variable=self.mining_mode, value="single", font=("Consolas", 9), bg=COLORS['bg_panel'], fg=COLORS['text_primary'], selectcolor=COLORS['bg_dark'], activebackground=COLORS['bg_panel'], activeforeground=COLORS['accent_green']).pack(side="left")

        # Depth
        tk.Label(grid_frame, text="Depth:", font=("Consolas", 9, "bold"), bg=COLORS['bg_panel'], fg=COLORS['text_secondary'], anchor="e").grid(row=2, column=0, sticky="e", padx=5, pady=8)
        depth_frame = tk.Frame(grid_frame, bg=COLORS['bg_panel'])
        depth_frame.grid(row=2, column=1, sticky="w", padx=5, pady=8)
        self.contracts_back_spin = tk.Spinbox(depth_frame, from_=0, to=20, width=5, font=("Consolas", 10))
        self.contracts_back_spin.delete(0, tk.END); self.contracts_back_spin.insert(0, "4")
        self.contracts_back_spin.pack(side="left")
        tk.Label(depth_frame, text="contracts back", bg=COLORS['bg_panel'], fg=COLORS['text_muted'], font=("Consolas", 8)).pack(side="left", padx=5)

        # Stop Loss
        tk.Label(grid_frame, text="Stop after X failures:", font=("Consolas", 9, "bold"), bg=COLORS['bg_panel'], fg=COLORS['text_secondary'], anchor="e").grid(row=3, column=0, sticky="e", padx=5, pady=8)
        stop_frame = tk.Frame(grid_frame, bg=COLORS['bg_panel'])
        stop_frame.grid(row=3, column=1, sticky="w", padx=5, pady=8)
        self.stop_loss_spin = tk.Spinbox(stop_frame, from_=3, to=30, width=5, font=("Consolas", 10))
        self.stop_loss_spin.delete(0, tk.END); self.stop_loss_spin.insert(0, "5")
        self.stop_loss_spin.pack(side="left")

        # === RIGHT PANEL: Log ===
        right_panel = tk.Frame(main_container, bg=COLORS['bg_panel'])
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)
        
        log_title = tk.Label(right_panel, text="ACTIVITY LOG", font=("Consolas", 11, "bold"), bg=COLORS['bg_panel'], fg=COLORS['accent_gold'], anchor="w")
        log_title.pack(fill="x", padx=15, pady=(15, 10))
        
        self.log = scrolledtext.ScrolledText(right_panel, height=20, font=("Consolas", 9), bg=COLORS['bg_dark'], fg=COLORS['accent_green'], state="disabled")
        self.log.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # === CONTROL PANEL ===
        control_panel = tk.Frame(root, bg=COLORS['bg_medium'], height=80)
        control_panel.pack(fill="x", padx=0, pady=0)
        
        progress_container = tk.Frame(control_panel, bg=COLORS['bg_medium'])
        progress_container.pack(fill="x", padx=20, pady=(15, 5))
        self.progress = ttk.Progressbar(progress_container, mode='determinate')
        self.progress.pack(fill="x")
        self.progress_label = tk.Label(progress_container, text="READY", font=("Consolas", 9, "bold"), bg=COLORS['bg_medium'], fg=COLORS['text_secondary'])
        self.progress_label.pack()
        
        btn_container = tk.Frame(control_panel, bg=COLORS['bg_medium'])
        btn_container.pack(pady=(0, 15))
        self.start_btn = self._create_action_button(btn_container, "▶ START MINING", self.start_download, COLORS['success'])
        self.start_btn.pack(side="left", padx=2)
        self.stop_btn = self._create_action_button(btn_container, "⬛ STOP", self.stop_download, COLORS['danger'])
        self.stop_btn.pack(side="left", padx=2)
        self.stop_btn.config(state="disabled")

        self.write_log("System Ready. Uses Direct Window Automation (V2).")

        self.is_running = False
        self.stop_requested = False
        self.desktop = Desktop(backend="uia")

    def _get_contracts(self):
        contracts = [
            "CL 03-26", "ES 03-26", "GC 04-26", "MES 03-26", "MNQ 03-26", "NQ 03-26", "RTY 03-26", "YM 03-26",
            "ES 06-26", "MNQ 06-26", "MNQ 12-25", "MNQ 09-25", "MNQ 06-25", "MNQ 03-25" 
        ]
        contracts.sort()
        return contracts

    def _create_action_button(self, parent, text, command, fg_color):
        return tk.Button(parent, text=text, command=command, font=("Consolas", 10, "bold"), bg=COLORS['bg_dark'], fg=fg_color, relief="raised", bd=3, width=15, height=1)

    def write_log(self, msg):
        def _write():
            self.log.config(state="normal")
            self.log.insert(tk.END, f"{msg}\n")
            self.log.see(tk.END)
            self.log.config(state="disabled")
        self.root.after(0, _write)

    def start_download(self):
        self.is_running = True
        self.stop_requested = False
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self.mining_worker, daemon=True).start()

    def stop_download(self):
        self.write_log("\n! STOP REQUESTED")
        self.stop_requested = True

    def _find_controls(self):
        """Locate NT8 controls using pywinauto"""
        try:
            window = self.desktop.window(title_re="^Historical Data.*")
            if not window.exists():
                return None, None, None
            
            # Find Edits
            edits = window.descendants(control_type="Edit")
            inst_edit = None
            date_edits = []
            
            date_pattern = re.compile(r'\d{1,2}/\d{1,2}/\d{4}')
            
            for edit in edits:
                text = edit.window_text()
                # Simple heuristic: if it looks like a date, it's a date field
                if date_pattern.search(text):
                    date_edits.append(edit)
                else:
                    # If it's valid instrument text or just the first non-date edit
                    if not inst_edit: 
                        inst_edit = edit
            
            # Find Download Button
            try:
                dl_btn = window.child_window(title="Download", control_type="Button")
            except:
                dl_btn = None
                
            return window, inst_edit, date_edits, dl_btn
        except Exception as e:
            self.write_log(f"Control search error: {e}")
            return None, None, None, None

    def _check_error_popup(self):
        """Checks if the FOREGROUND window is an error popup and closes it."""
        try:
            # Low-level approach: What is the user actually looking at?
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            buff = ctypes.create_unicode_buffer(length + 1)
            ctypes.windll.user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value
            
            # If the active window is the Error popup, nuke it.
            # Usually "Error" or "NinjaTrader"
            if title == "Error" or title == "NinjaTrader":
                
                # Check for "Historical Data" title to AVOID killing main window
                if "Historical Data" in title:
                    return False
                
                self.write_log(f"  ⚠ Active Popup detected: '{title}'. DISMISSING.")
                
                # Active window is the popup. Just press Enter.
                time.sleep(0.1) 
                pyautogui.press('enter')
                time.sleep(0.1)
                
                # Verify it's gone. If not, ESC.
                hwnd_new = ctypes.windll.user32.GetForegroundWindow()
                if hwnd == hwnd_new:
                     pyautogui.press('escape')
                
                return True
                
        except Exception as e:
            pass
        return False

    def mining_worker(self):
        try:
            if self.stop_requested: return
            
            # Configuration
            try: max_contracts_back = int(self.contracts_back_spin.get())
            except: max_contracts_back = 4
            try: stop_loss_limit = int(self.stop_loss_spin.get())
            except: stop_loss_limit = 5
            
            current_contract = self.inst_combo.get().strip()
            contracts_processed = 0
            
            self.write_log(f"\n{'='*50}")
            self.write_log("⚡ STARTING DEEP HISTORY MINE (V2 AUTO) ⚡")
            
            while contracts_processed <= max_contracts_back and not self.stop_requested:
                self.write_log(f"\n>>> PROCESSING CONTRACT: {current_contract}")
                
                # Verify Window Connection
                window, inst_edit, date_edits, dl_btn = self._find_controls()
                if not window:
                    self.write_log("ERROR: Historical Data window not found!")
                    break
                if not inst_edit or not dl_btn:
                    self.write_log("ERROR: Could not find Instrument input or Download button.")
                    break
                
                # Bring to front once
                try: window.set_focus()
                except: pass
                
                # Set Instrument
                self.write_log(f"Setting Instrument: {current_contract}")
                inst_edit.set_edit_text(current_contract)
                time.sleep(0.5)

                # Determine Start Date
                if contracts_processed == 0:
                    start_date = date.today() - timedelta(days=1)
                else:
                    start_date = get_contract_expiry(current_contract)
                
                current_date = start_date
                consecutive_misses = 0
                downloaded_count = 0
                
                self.write_log(f"Mining backwards from: {current_date}")
                
                while consecutive_misses < stop_loss_limit and not self.stop_requested:
                    if current_date.weekday() == 5: # Skip Saturday
                        current_date -= timedelta(days=1)
                        continue
                    
                    date_str = current_date.strftime("%m/%d/%Y")
                    self.write_log(f"Checking {date_str}...")
                    
                    # === SCAN EXISTING DATA FIRST ===
                    year = current_date.year
                    month = str(current_date.month).zfill(2)
                    day = str(current_date.day).zfill(2)
                    expected_filename = f"{year}{month}{day}.nrd"
                    docs_path = os.path.join(os.path.expanduser("~"), "Documents")
                    replay_path = os.path.join(docs_path, "NinjaTrader 8", "db", "replay", current_contract, expected_filename)
                    
                    if os.path.exists(replay_path):
                        self.write_log(f"  ✓ Already Exists (Skip)")
                        downloaded_count += 1
                        current_date -= timedelta(days=1)
                        self.progress_label.config(text=f"Total: {downloaded_count} | Streak: {consecutive_misses}")
                        continue
                    
                    # Set Date
                    for de in date_edits:
                        try: de.set_edit_text(date_str)
                        except: pass
                    
                    # === ROBUST BUTTON CLICK & REACTION CHECK ===
                    
                    # 1. Wait until button is enabled
                    wait_ready = 0
                    while not dl_btn.is_enabled() and wait_ready < 5:
                        # Also check for popup here, in case previous one lingered?
                        if self._check_error_popup(): 
                            self.write_log("  (Cleared lingering popup)")
                        
                        time.sleep(0.5)
                        wait_ready += 0.5
                    
                    # 2. Click Download
                    try:
                        if dl_btn.is_enabled():
                            dl_btn.click()
                        else:
                            self.write_log("Warning: Button disabled, attempting invoke...")
                            dl_btn.invoke()
                    except Exception as e:
                        self.write_log(f"Click Exception: {e}")

                    # 3. POLL FOR OUTCOME (Critical Phase)
                    # We expect either:
                    # A) Button Disables (Download Started) -> Good
                    # B) Error Popup Appears (No Data) -> Bad/Miss
                    # C) Nothing happens (Timeout) -> Bad
                    
                    outcome = "unknown"
                    poll_duration = 0
                    while poll_duration < 3.0:
                        # Check Error
                        if self._check_error_popup():
                            outcome = "error"
                            break
                        
                        # Check Button State (Disabled = Started)
                        if not dl_btn.is_enabled():
                            outcome = "started"
                            break
                            
                        time.sleep(0.1)
                        poll_duration += 0.1
                        
                    if outcome == "error":
                        consecutive_misses += 1
                        self.progress_label.config(text=f"Total: {downloaded_count} | Streak: {consecutive_misses} (Error Popup)")
                        # We handled the popup inside _check_error_popup
                        
                    elif outcome == "started":
                        # 4. Wait for download to finish (Button becomes Enabled again)
                        wait_download = 0
                        while not dl_btn.is_enabled():
                            if self.stop_requested: break
                            
                            # Just in case an error pops up LATE (weird, but possible)
                            if self._check_error_popup():
                                outcome = "error_late"
                                break
                                
                            time.sleep(0.5)
                            wait_download += 0.5
                            if wait_download > 300: # 5 minutes max
                                self.write_log(f"Timeout waiting for download finish (> 5m)")
                                break
                        
                        if outcome == "error_late":
                            consecutive_misses += 1
                            self.progress_label.config(text=f"Total: {downloaded_count} | Streak: {consecutive_misses} (Late Error)")
                        else:
                            # Success!
                            self.write_log(f"  ✓ SUCCESS")
                            consecutive_misses = 0 
                            downloaded_count += 1
                            time.sleep(1.0) # Throttle as requested
                            
                    else:
                        # Timeout / Unknown state
                        self.write_log("  ? No reaction from button/app.")
                        # Could be instant download? Check file
                        time.sleep(0.5)
                        if os.path.exists(replay_path):
                            self.write_log("  (File found despite no UI reaction)")
                            downloaded_count += 1
                            consecutive_misses = 0
                        else:
                            consecutive_misses += 1

                    current_date -= timedelta(days=1)
                    self.progress_label.config(text=f"Total: {downloaded_count} | Streak: {consecutive_misses}")

                self.write_log(f"Finished {current_contract}. Downloaded: {downloaded_count}")
                
                if self.mining_mode.get() == "single":
                    break
                    
                current_contract = get_previous_contract(current_contract)
                contracts_processed += 1
                
            self.write_log("\n✓ MINING COMPLETE")

        except Exception as e:
            self.write_log(f"CRITICAL CRASH: {e}")
            import traceback
            self.write_log(traceback.format_exc())
            messagebox.showerror("Crash Detected", f"An error occurred:\n{e}")
        finally:
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.is_running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingTerminalGUI(root)
    root.mainloop()
