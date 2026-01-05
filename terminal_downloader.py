import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import pyautogui
import time
from datetime import timedelta, date
import os
import glob
from contract_utils import get_active_trading_period, get_previous_contract, get_contract_expiry
from PIL import Image, ImageTk 

pyautogui.FAILSAFE = True

# Professional Trading Terminal Color Scheme
COLORS = {
    'bg_dark': '#0a1612',           # Very dark green-black
    'bg_medium': '#0d2117',         # Dark green
    'bg_panel': '#162d22',          # Panel background
    'accent_green': '#00ff41',      # Matrix green
    'accent_gold': '#ffd700',       # Gold accent
    'text_primary': '#e0ffe0',      # Light green text
    'text_secondary': '#80c080',    # Medium green text
    'text_muted': '#506850',        # Muted green
    'success': '#00ff41',           # Bright green
    'warning': '#ffb900',           # Orange warning
    'danger': '#ff4444',            # Red
    'button_bg': '#1e4d2b',         # Button background
    'button_active': '#00ff41',     # Active button
}

class TradingTerminalGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NT8 MARKET REPLAY TERMINAL - DEEP HISTORY")
        # Increase window width/height to accommodate larger image
        self.root.geometry("1100x1000")
        self.root.configure(bg=COLORS['bg_dark'])
        
        # Custom style
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure('Terminal.TCombobox', 
                       fieldbackground=COLORS['bg_panel'],
                       background=COLORS['bg_panel'],
                       foreground=COLORS['text_primary'],
                       arrowcolor=COLORS['accent_green'])
        
        self.download_button_coords = None
        self.date_field_coords = None
        self.download_button_coords = None
        self.instrument = None
        self.existing_dates = set()
        
        # === HEADER ===
        header = tk.Frame(root, bg=COLORS['bg_medium'], height=60)
        header.pack(fill="x", padx=0, pady=0)
        
        title = tk.Label(header, text="⚡ NT8 DEEP HISTORY MINER",
                        font=("Consolas", 18, "bold"),
                        bg=COLORS['bg_medium'],
                        fg=COLORS['accent_green'])
        title.pack(pady=15)
        
        # === INSTRUCTIONS CANVAS (Top) ===
        # Use a canvas to draw image and overlay text
        # Adjust height as needed to fit the image
        canvas_height = 200 
        self.instr_canvas = tk.Canvas(root, bg=COLORS['bg_panel'], height=canvas_height, highlightthickness=0)
        self.instr_canvas.pack(fill="x", padx=10, pady=(10, 5))
        
        # Load and resize image
        self.photo = None
        image_loaded = False
        try:
            img_path = "helper_preview.png"
            if os.path.exists(img_path):
                raw_img = Image.open(img_path)
                
                # We want it to span the width (approx 1080px with padding)
                target_width = 1080
                
                # Calculate height to keep aspect ratio
                w_percent = (target_width / float(raw_img.size[0]))
                h_size = int((float(raw_img.size[1]) * float(w_percent)))
                
                # Update canvas height to fit image if it's taller, or clip if extremely tall?
                # User asked to "display it entirely".
                if h_size > canvas_height:
                    self.instr_canvas.config(height=h_size)
                    canvas_height = h_size
                
                raw_img = raw_img.resize((target_width, h_size), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(raw_img)
                
                # Draw image at top-left
                self.instr_canvas.create_image(0, 0, image=self.photo, anchor="nw")
                image_loaded = True
        except Exception as e:
            print(f"Could not load image: {e}")
            self.instr_canvas.create_text(540, 100, text="(Image not found)", fill="white")

        # Overlay text
        # User asked for instruction text as an overlay.
        # We need high contrast so we'll use a semi-transparent looking hack: Text with a shadow.
        
        instruction_lines = [
            "Step-by-Step Instructions",
            "Open Tools -> Historical Data -> Market Replay",
            "Hover over download button to lock coordinates",
            "Select the 'Instrument' text field manually & Click Start",
            "App will handle tabbing logic automatically"
        ]
        
        # Center text horizontally (window width 1100, so center ~550)
        text_center_x = 550
        text_start_y = 20
        line_height = 25
        
        # Draw Text (Centered, Transparent Background)
        for i, line in enumerate(instruction_lines):
            y = text_start_y + (i * line_height)
            # Header styling
            if i == 0:
                font_spec = ("Consolas", 12, "bold")
                color = COLORS['accent_gold']
            else:
                font_spec = ("Consolas", 9, "bold")
                color = "white" # High contrast on image
                
            # Add a subtle shadow for readability on any image
            self.instr_canvas.create_text(
                text_center_x + 1, y + 1,
                text=line, anchor="center",
                font=font_spec, fill="black"
            )
            self.instr_canvas.create_text(
                text_center_x, y,
                text=line, anchor="center",
                font=font_spec, fill=color
            )

        # === MAIN CONTAINER ===
        main_container = tk.Frame(root, bg=COLORS['bg_dark'])
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # === LEFT PANEL: Configuration ===
        left_panel = tk.Frame(main_container, bg=COLORS['bg_panel'], width=450)
        left_panel.pack(side="left", fill="both", padx=(0, 5), pady=0)
        
        config_title = tk.Label(left_panel, text="▸ CONFIGURATION",
                               font=("Consolas", 11, "bold"),
                               bg=COLORS['bg_panel'],
                               fg=COLORS['accent_gold'],
                               anchor="w")
        config_title.pack(fill="x", padx=15, pady=(15, 10))
        
        # Grid Container
        grid_frame = tk.Frame(left_panel, bg=COLORS['bg_panel'])
        grid_frame.pack(fill="x", padx=15, pady=5)
        
        # Configure Grid Columns
        grid_frame.columnconfigure(0, weight=1) # Labels
        grid_frame.columnconfigure(1, weight=2) # Inputs

        # --- ROW 0: Contract ---
        tk.Label(grid_frame, text="Starting Contract:", font=("Consolas", 9, "bold"), bg=COLORS['bg_panel'], fg=COLORS['text_secondary'], anchor="e").grid(row=0, column=0, sticky="e", padx=5, pady=8)
        
        contracts = self._get_contracts()
        self.inst_combo = ttk.Combobox(grid_frame, values=contracts, width=18, font=("Consolas", 10), style='Terminal.TCombobox')
        self.inst_combo.set("MNQ 03-26")
        self.inst_combo.grid(row=0, column=1, sticky="w", padx=5, pady=8)
        
        # --- ROW 1: Mode ---
        tk.Label(grid_frame, text="Mining Mode:", font=("Consolas", 9, "bold"), bg=COLORS['bg_panel'], fg=COLORS['text_secondary'], anchor="e").grid(row=1, column=0, sticky="e", padx=5, pady=8)
        
        mode_frame = tk.Frame(grid_frame, bg=COLORS['bg_panel'])
        mode_frame.grid(row=1, column=1, sticky="w", padx=5, pady=8)
        self.mining_mode = tk.StringVar(value="deep")
        tk.Radiobutton(mode_frame, text="Deep History", variable=self.mining_mode, value="deep", font=("Consolas", 9), bg=COLORS['bg_panel'], fg=COLORS['text_primary'], selectcolor=COLORS['bg_dark'], activebackground=COLORS['bg_panel'], activeforeground=COLORS['accent_green']).pack(side="left")
        
        # --- ROW 2: Depth ---
        tk.Label(grid_frame, text="Depth:", font=("Consolas", 9, "bold"), bg=COLORS['bg_panel'], fg=COLORS['text_secondary'], anchor="e").grid(row=2, column=0, sticky="e", padx=5, pady=8)
        
        depth_frame = tk.Frame(grid_frame, bg=COLORS['bg_panel'])
        depth_frame.grid(row=2, column=1, sticky="w", padx=5, pady=8)
        self.contracts_back_spin = tk.Spinbox(depth_frame, from_=0, to=20, width=5, font=("Consolas", 10))
        self.contracts_back_spin.delete(0, tk.END)
        self.contracts_back_spin.insert(0, "4")
        self.contracts_back_spin.pack(side="left")
        tk.Label(depth_frame, text="contracts back", bg=COLORS['bg_panel'], fg=COLORS['text_muted'], font=("Consolas", 8)).pack(side="left", padx=5)

        # --- ROW 3: Stop Loss ---
        tk.Label(grid_frame, text="Stop Loss:", font=("Consolas", 9, "bold"), bg=COLORS['bg_panel'], fg=COLORS['text_secondary'], anchor="e").grid(row=3, column=0, sticky="e", padx=5, pady=8)
        
        stop_frame = tk.Frame(grid_frame, bg=COLORS['bg_panel'])
        stop_frame.grid(row=3, column=1, sticky="w", padx=5, pady=8)
        self.stop_loss_spin = tk.Spinbox(stop_frame, from_=3, to=30, width=5, font=("Consolas", 10))
        self.stop_loss_spin.delete(0, tk.END)
        self.stop_loss_spin.insert(0, "5")
        self.stop_loss_spin.pack(side="left")
        tk.Label(stop_frame, text="misses in a row", bg=COLORS['bg_panel'], fg=COLORS['text_muted'], font=("Consolas", 8)).pack(side="left", padx=5)
        
        # --- ROW 4: Timeout ---
        tk.Label(grid_frame, text="Timeout:", font=("Consolas", 9, "bold"), bg=COLORS['bg_panel'], fg=COLORS['text_secondary'], anchor="e").grid(row=4, column=0, sticky="e", padx=5, pady=8)
        
        time_frame = tk.Frame(grid_frame, bg=COLORS['bg_panel'])
        time_frame.grid(row=4, column=1, sticky="w", padx=5, pady=8)
        self.wait_spinbox = tk.Spinbox(time_frame, from_=3, to=60, width=5, font=("Consolas", 10))
        self.wait_spinbox.delete(0, tk.END)
        self.wait_spinbox.insert(0, "8")
        self.wait_spinbox.pack(side="left")
        tk.Label(time_frame, text="seconds", bg=COLORS['bg_panel'], fg=COLORS['text_muted'], font=("Consolas", 8)).pack(side="left", padx=5)

        # === SETUP BUTTONS (Below Grid) ===
        tk.Label(left_panel, text="SETUP", font=("Consolas", 11, "bold"), bg=COLORS['bg_panel'], fg=COLORS['accent_gold'], anchor="w").pack(fill="x", padx=15, pady=(20, 10))
        
        btn_frame = tk.Frame(left_panel, bg=COLORS['bg_panel'])
        btn_frame.pack(fill="x", padx=15)
        
        self.find_btn = self._create_button(btn_frame, "📍 HOVER OVER DOWNLOAD BUTTON", self.calibrate_positions, COLORS['button_bg'])
        self.find_btn.pack(fill="x", pady=2)
        
        self.coord_status = tk.Label(left_panel, text="⊗ Positions: Not Set", font=("Consolas", 9), bg=COLORS['bg_panel'], fg=COLORS['danger'], anchor="w")
        self.coord_status.pack(fill="x", padx=15, pady=(5, 10))

        # === RIGHT PANEL: Log ===
        right_panel = tk.Frame(main_container, bg=COLORS['bg_panel'])
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0), pady=0)
        
        log_title = tk.Label(right_panel, text="▸ ACTIVITY LOG", font=("Consolas", 11, "bold"), bg=COLORS['bg_panel'], fg=COLORS['accent_gold'], anchor="w")
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

        self.write_log("⚡ DEEP HISTORY MINER ACTIVATE")
        self.write_log("→ Select 'Deep History' to mine backwards through contracts.")

        self.is_running = False
        self.stop_requested = False

    def _get_contracts(self):
        contracts = [
            "CL 03-26", "ES 03-26", "GC 04-26", "MES 03-26", "MNQ 03-26", "NQ 03-26", "RTY 03-26", "YM 03-26",
            "ES 06-26", "MNQ 06-26",
            "MNQ 12-25", "MNQ 09-25", "MNQ 06-25", "MNQ 03-25" 
        ]
        contracts.sort()
        return contracts

    def _create_label_row(self, parent, text):
        tk.Label(parent, text=text, font=("Consolas", 9, "bold"), bg=COLORS['bg_panel'], fg=COLORS['text_secondary'], anchor="w").pack(fill="x", padx=15, pady=(5, 3))
    def _create_radio(self, parent, text, value, variable):
        tk.Radiobutton(parent, text=text, variable=variable, value=value, font=("Consolas", 10), bg=COLORS['bg_panel'], fg=COLORS['text_primary'], selectcolor=COLORS['bg_dark'], activebackground=COLORS['bg_panel'], activeforeground=COLORS['accent_green']).pack(side="left", padx=(0, 15))
    def _create_button(self, parent, text, command, bg_color):
        return tk.Button(parent, text=text, command=command, font=("Consolas", 10, "bold"), bg=bg_color, fg=COLORS['text_primary'], relief="raised", bd=2)
    def _create_action_button(self, parent, text, command, fg_color):
        return tk.Button(parent, text=text, command=command, font=("Consolas", 10, "bold"), bg=COLORS['bg_dark'], fg=fg_color, relief="raised", bd=3, width=15, height=1)

    def write_log(self, msg):
        def _write():
            self.log.config(state="normal")
            self.log.insert(tk.END, f"{msg}\n")
            self.log.see(tk.END)
            self.log.config(state="disabled")
        self.root.after(0, _write)

    def calibrate_positions(self):
        self.write_log("\n=== CALIBRATION WIZARD ===")
        self.write_log("Position mouse over DOWNLOAD BUTTON")
        
        def worker():
            for i in range(5, 0, -1):
                self.write_log(f"  {i}...")
                time.sleep(1)
            pos = pyautogui.position()
            self.download_button_coords = (pos.x, pos.y)
            self.write_log(f"✓ DOWNLOAD button captured: {pos.x}, {pos.y}")
            
            self.root.after(0, lambda: self.coord_status.config(text=f"✓ Set: Button({pos.x},{pos.y})", fg=COLORS['success']))
            self.write_log("Calibration Complete! Ready to Mine.")

        threading.Thread(target=worker, daemon=True).start()

    def start_download(self):
        if self.download_button_coords is None:
            messagebox.showerror("Error", "Run Calibration first!")
            return
        
        self.is_running = True
        self.stop_requested = False
        self.start_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        threading.Thread(target=self.mining_worker, daemon=True).start()

    def stop_download(self):
        self.write_log("\n! STOP REQUESTED")
        self.stop_requested = True

    def mining_worker(self):
        try:
            if self.stop_requested: return
            
            # Safe Value Getting
            try:
                max_contracts_back = int(self.contracts_back_spin.get())
            except:
                max_contracts_back = 4
                
            try:
                stop_loss_limit = int(self.stop_loss_spin.get())
            except:
                stop_loss_limit = 5
                
            try:
                wait_time_setting = int(self.wait_spinbox.get())
            except:
                wait_time_setting = 8
            
            current_contract = self.inst_combo.get().strip()
            contracts_processed = 0
            
            self.write_log(f"\n{'='*50}")
            self.write_log("⚡ STARTING DEEP HISTORY MINE ⚡")
            self.write_log(f"Start Contract: {current_contract}")
            
            pyautogui.alert('Click OK, then IMMEDIATELY click the INSTRUMENT field.', 'Ready?')
            time.sleep(3) # Give user time to click instrument

            while contracts_processed <= max_contracts_back and not self.stop_requested:
                self.write_log(f"\n>>> PROCESSING CONTRACT: {current_contract}")
                
                # We assume cursor is in Instrument field (or Date field at start of loop)
                # To be safe, we always reset: Tab from Instrument to Date
                
                # 1. Type Instrument
                pyautogui.hotkey('ctrl', 'a') 
                time.sleep(0.1)
                pyautogui.write(current_contract, interval=0.1)
                time.sleep(0.5)
                
                # Tab to Date
                pyautogui.press('tab') 
                time.sleep(0.5)

                # 2. Determine Start Date
                if contracts_processed == 0:
                    start_date = date.today() - timedelta(days=1) # Yesterday
                else:
                    start_date = get_contract_expiry(current_contract)
                
                current_date = start_date
                consecutive_misses = 0
                downloaded_count = 0
                
                self.write_log(f"Mining backwards from: {current_date}")
                
                # 3. Mine Backwards
                while consecutive_misses < stop_loss_limit and not self.stop_requested:
                    if current_date.weekday() == 5: # Skip Saturday
                        current_date -= timedelta(days=1)
                        continue
                    
                    date_str = current_date.strftime("%m/%d/%Y")
                    self.write_log(f"Checking {date_str}...")
                    
                    # Type Date (We are in Date Field)
                    pyautogui.hotkey('ctrl', 'a')
                    time.sleep(0.1)
                    pyautogui.write(date_str, interval=0.05)
                    time.sleep(0.5)
                    
                    # Tab to Download Button (Usually 2 tabs from Date?)
                    # Let's try explicit click since we have the coord!
                    # BUT user wants to verify logic. 
                    # Use click to be safe, then Shift-Tab back to Date.
                    
                    pyautogui.click(self.download_button_coords)
                    
                    # Wait for File
                    year = current_date.year
                    month = str(current_date.month).zfill(2)
                    day = str(current_date.day).zfill(2)
                    expected_filename = f"{year}{month}{day}.nrd"
                    
                    # Robust System Path
                    docs_path = os.path.join(os.path.expanduser("~"), "Documents")
                    replay_path = os.path.join(docs_path, "NinjaTrader 8", "db", "replay", current_contract, expected_filename)
                    
                    # Poll
                    poll_count = 0
                    found = False
                    while poll_count < (wait_time_setting * 2):
                        if os.path.exists(replay_path):
                            found = True
                            break
                        if self.stop_requested: break
                        time.sleep(0.5)
                        poll_count += 1
                        
                    # Handle Result
                    if found:
                        self.write_log(f"  ✓ SUCCESS")
                        consecutive_misses = 0 
                        downloaded_count += 1
                    else:
                        self.write_log(f"  X No Data / Timeout")
                        consecutive_misses += 1
                    
                    # Dismiss Popup
                    pyautogui.press('enter')
                    time.sleep(0.2)
                    pyautogui.press('escape')
                    time.sleep(0.2)
                    
                    # Return to Date Field
                    # We clicked the button, so focus is on button.
                    # NEED TO SHIFT+TAB BACK TO DATE FIELD
                    # Usually 2 or 3 tabs depending on UI. 
                    # Safe bet: Shift+Tab 3 times to be sure, or just click instrument again?
                    # User requested 'perfect logic earlier'. 
                    # Let's use Shift+Tab x3
                    for _ in range(3):
                        pyautogui.hotkey('shift', 'tab')
                        time.sleep(0.1)

                    current_date -= timedelta(days=1) # Go backwards
                    self.progress_label.config(text=f"Total: {downloaded_count} | Streak: {consecutive_misses}")

                self.write_log(f"Finished {current_contract}. Downloaded: {downloaded_count}")
                
                if self.mining_mode.get() == "single":
                    break
                    
                # Prepare for next contract
                current_contract = get_previous_contract(current_contract)
                contracts_processed += 1
                
                # We are currently in Date field (from loop end).
                # Shift+Tab ONCE to get back to Instrument field
                pyautogui.hotkey('shift', 'tab')
                time.sleep(0.5)

            self.write_log("\n✓ MINING COMPLETE")

        except Exception as e:
            self.write_log(f"ERROR: {e}")
            import traceback
            self.write_log(traceback.format_exc())
        finally:
            self.start_btn.config(state="normal")
            self.stop_btn.config(state="disabled")
            self.is_running = False

if __name__ == "__main__":
    root = tk.Tk()
    app = TradingTerminalGUI(root)
    root.mainloop()
