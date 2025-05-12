import tkinter as tk
from tkinter import messagebox, ttk, Toplevel, Label, Entry, Button, StringVar, OptionMenu, messagebox, Frame, Radiobutton, IntVar
from datetime import datetime, timedelta, date
from PIL import ImageTk, Image
import base64
import io
import requests
import os
import sys
import tempfile
import time
from tkinter.scrolledtext import ScrolledText
import json
import webbrowser
import requests
import polyline
import math
from concurrent.futures import ThreadPoolExecutor, as_completed
import re
from geopy.geocoders import Nominatim
from functools import lru_cache
from pathlib import Path
import numpy as np
import xml.etree.ElementTree as ET
import urllib.parse
import atexit
import subprocess
import traceback
from geopy.distance import geodesic
import shutil
from dateutil import parser
from collections import defaultdict



refresh_dropdown_global = None
density_calculator_window = None

documents_folder = os.path.join(os.path.expanduser("~"), "Documents", "Transit Time Calculator")
log_path = os.path.join(documents_folder, "eta_log.txt")

os.makedirs(documents_folder, exist_ok=True)

class LogRedirector:
    def __init__(self, logfile_path):
        self.terminal = sys.__stdout__  # just in case sys.stdout is already redirected
        try:
            self.log = open(logfile_path, "a", encoding="utf-8-sig", buffering=1)
        except Exception as e:
            self.log = None
            print(f"❌ Failed to open log file: {e}")

    def write(self, message):
        try:
            if self.terminal:
                self.terminal.write(message)
            if self.log:
                if message.strip():
                    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S] ")
                    for line in message.rstrip().splitlines():
                        self.log.write(f"{timestamp}{line}\n")
                elif message == "\n":
                    self.log.write("\n")
        except Exception as e:
            pass  # Silent fail to avoid crashing UI

    def flush(self):
        try:
            if self.terminal:
                self.terminal.flush()
            if self.log:
                self.log.flush()
        except:
            pass

sys.stdout = LogRedirector(log_path)
sys.stderr = sys.stdout


# Custom logging wrappers for consistent output across the application.
# Used for debugging, tracing logic flow, and surfacing warnings.

def log_info(message):
    print(f"[INFO] {message}")

def log_warning(message):
    print(f"[WARNING] {message}")

def log_error(message):
    print(f"[ERROR] {message}")

def log_debug(message):
    print(f"[DEBUG] {message}")



us_state_abbr = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
    "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
    "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD", "Massachusetts": "MA",
    "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO", "Montana": "MT",
    "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
    "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
    "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}


theme_options = {
    "Light Mode": {"bg": "white", "fg": "black"},
    "Dark Mode": {"bg": "#202020", "fg": "white"},
    "Slate Gray": {"bg": "darkgray", "fg": "black"},
    "Midnight Blue": {"bg": "#191970", "fg": "white"},
    "Forest Green": {"bg": "#228B22", "fg": "white"},
    "Royal Purple": {"bg": "#6A0DAD", "fg": "white"},
    "Steel Blue": {"bg": "#4682B4", "fg": "white"},
    "Desert Tan": {"bg": "#D2B48C", "fg": "black"},
    "Sky Blue": {"bg": "#87CEEB", "fg": "black"},
    "Crimson": {"bg": "#DC143C", "fg": "white"},

    "Coral Sunset": {"bg": "#FF6F61", "fg": "white"},
    "Cool Teal": {"bg": "#008080", "fg": "white"},
    "Sunburst Orange": {"bg": "#FFA500", "fg": "#2E1A00"},
    "Neon Green": {"bg": "#39FF14", "fg": "#000000"},
    "Hot Pink Punch": {"bg": "#FF69B4", "fg": "#2F004F"},
    "Aqua Splash": {"bg": "#00FFFF", "fg": "#004040"},

    "Mint Cream": {"bg": "#F5FFFA", "fg": "#003366"},
    "Pastel Peach": {"bg": "#FFDAB9", "fg": "#5C4033"},
    "Lavender Mist": {"bg": "#E6E6FA", "fg": "#4B0082"},
    "Soft Lilac": {"bg": "#D8BFD8", "fg": "#333333"},
    "Powder Blue": {"bg": "#B0E0E6", "fg": "#003366"},
    "Wheat Beige": {"bg": "#F5DEB3", "fg": "#3C2F2F"},

    "Charcoal Glow": {"bg": "#36454F", "fg": "#FFD700"},
    "High Contrast": {"bg": "#000000", "fg": "#FFFF00"},
    "Obsidian": {"bg": "#0B0C10", "fg": "#C5C6C7"},
    "Graphite": {"bg": "#2F4F4F", "fg": "#F8F8FF"},
    "Deep Sea Blue": {"bg": "#001F3F", "fg": "#7FDBFF"},
}




FREIGHT_CLASS_TABLE = {
    "Paper Goods": {
        "nmfc": "153900",
        "density_based": True,
        "density_map": [
            (1, "Class 400", "Sub-01"), (2, "Class 300", "Sub-02"),
            (4, "Class 250", "Sub-03"), (6, "Class 175", "Sub-04"),
            (8, "Class 125", "Sub-05"), (10, "Class 100", "Sub-06"),
            (12, "Class 92.5", "Sub-07"), (15, "Class 85", "Sub-08"),
            (22.5, "Class 70", "Sub-09"), (30, "Class 65", "Sub-10"),
            (9999, "Class 60", "Sub-11")
        ]
    },
    "Plastic Articles": {
        "nmfc": "156600",
        "density_based": True,
        "density_map": [
            (1, "Class 400", "Sub-01"), (2, "Class 300", "Sub-02"),
            (4, "Class 250", "Sub-03"), (6, "Class 175", "Sub-04"),
            (8, "Class 125", "Sub-05"), (10, "Class 100", "Sub-06"),
            (12, "Class 92.5", "Sub-07"), (15, "Class 85", "Sub-08"),
            (22.5, "Class 70", "Sub-09"), (30, "Class 65", "Sub-10"),
            (9999, "Class 60", "Sub-11")
        ]
    },
    "Machinery (Boxed)": {
        "nmfc": "133300",
        "density_based": True,
        "density_map": [
            (5, "Class 250", "Sub-02"), (10, "Class 125", "Sub-03"),
            (15, "Class 85", "Sub-04"), (9999, "Class 65", "Sub-05")
        ]
    },
    "Furniture": {
        "nmfc": "79300",
        "density_based": True,
        "density_map": [
            (1, "Class 400", "Sub-01"), (2, "Class 300", "Sub-02"),
            (4, "Class 250", "Sub-03"), (6, "Class 175", "Sub-04"),
            (8, "Class 125", "Sub-05"), (10, "Class 100", "Sub-06"),
            (12, "Class 92.5", "Sub-07"), (15, "Class 85", "Sub-08"),
            (22.5, "Class 70", "Sub-09"), (30, "Class 65", "Sub-10"),
            (9999, "Class 60", "Sub-11")
        ]
    },
    "Totes (IBC - Plastic)": {
        "nmfc": "41024",
        "density_based": False,
        "class_logic": "per_item_weight",
        "class_map": [
            (400, "Class 200", "Sub-02"),
            (999999, "Class 125", "Sub-03")
        ]
    },
    "Totes (IBC - KD Flat)": {
        "nmfc": "41024",
        "density_based": False,
        "class": "Class 70",
        "sub_code": "Sub-04"
    },
    "Totes (IBC - Metal)": {
        "nmfc": "41027",
        "density_based": False,
        "class": "Class 125",
        "sub_code": None
    },
    "Compounds - Cleaning": {
        "nmfc": "48580",
        "density_based": False,
        "class": "Class 70"
    },
    "Compounds - Mold Release": {
        "nmfc": "50244",
        "density_based": False,
        "class": "Class 60"
    },
    "Fabric (Rolled or Baled)": {
        "nmfc": "49260",
        "density_based": True,
        "density_map": [
            (1, "Class 400", "Sub-01"), 
            (2, "Class 300", "Sub-02"),
            (4, "Class 250", "Sub-03"),
            (6, "Class 175", "Sub-04"),
            (8, "Class 125", "Sub-05"),
            (10, "Class 100", "Sub-06"),
            (12, "Class 92.5", "Sub-07"),
            (15, "Class 85", "Sub-08"),
            (22.5, "Class 70", "Sub-09"),
            (30, "Class 65", "Sub-10"),
            (9999, "Class 60", "Sub-11")
        ]
    }
}




def apply_config_to_gui(config):
    if "default_origin" in config:
        entry_origin.delete(0, tk.END)
        entry_origin.insert(0, config["default_origin"])

    if "default_destination" in config:
        entry_destination.delete(0, tk.END)
        entry_destination.insert(0, config["default_destination"])

    if "default_unload_hours" in config:
        global DEFAULT_UNLOAD_TIME_HOURS
        DEFAULT_UNLOAD_TIME_HOURS = float(config["default_unload_hours"])

    if "default_detention_rate" in config:
        global DEFAULT_DETENTION_RATE
        DEFAULT_DETENTION_RATE = float(config["default_detention_rate"])

    if "default_mph" in config:
        global DEFAULT_AVERAGE_MPH
        DEFAULT_AVERAGE_MPH = float(config["default_mph"])
        entry_speed.delete(0, tk.END)
        mph = DEFAULT_AVERAGE_MPH
        entry_speed.insert(0, str(int(mph)) if mph == int(mph) else str(mph))

    if "selected_theme" in config:
        selected_theme = config["selected_theme"]
        if selected_theme in theme_options:
            colors = theme_options[selected_theme]
            root.config(bg=colors["bg"])
            for widget in root.winfo_children():
                try:
                    widget.config(bg=colors["bg"], fg=colors["fg"])
                except:
                    pass






def load_config():
    try:
        documents_folder = os.path.expanduser("~/Documents/Transit Time Calculator")
        config_path = os.path.join(documents_folder, "eta_config.json")

        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                return json.load(f)
    except Exception as e:
        print("Error loading config:", e)

    return {}
    
config = load_config()

MIN_SAMPLE_DISTANCE_MILES = float(config.get("default_weather_sample_spacing", 75.0))
smart_recommendations_enabled = config.get("smart_recommendations_enabled", True)



def save_config(config_data):
    try:
        documents_folder = os.path.expanduser("~/Documents/Transit Time Calculator")
        config_path = os.path.join(documents_folder, "eta_config.json")

        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=4)
    except Exception as e:
        print("Error saving config:", e)
        
        


def open_console_viewer():
    try:
        full_path = os.path.abspath(log_path)

        if shutil.which("wt"):
            # Prefer Windows Terminal with PowerShell
            command = [
                "wt",
                "powershell",
                "-NoExit",
                "-Command",
                f"Get-Content -Path '{full_path}' -Wait"
            ]
            log_info("Launching Windows Terminal viewer (emoji compatible)...")
            subprocess.Popen(command)
        else:
            # Fallback to cmd with UTF-8 — less emoji-friendly
            command = (
                f'start cmd /k "chcp 65001 > nul && '
                f'powershell -NoExit -Command Get-Content -Path \'{full_path}\' -Wait"'
            )
            log_info("Launching legacy CMD viewer (limited emoji support)...")
            subprocess.Popen(command, shell=True)

    except Exception as e:
        print("❌ Failed to open console window:", e)


def get_weather_sample_points():
    return load_config().get("weather_sample_points", 4)
    
documents_path = Path.home() / "Documents" / "Transit Time Calculator"
json_file_path = documents_path / "user_nmfc_data.json"
os.makedirs(documents_path, exist_ok=True)


def sample_coords_by_distance(decoded_coords, min_distance_miles=75, max_samples=10):
    if not decoded_coords or len(decoded_coords) < 2:
        return decoded_coords

    selected = [decoded_coords[0]]
    last_lat, last_lon = decoded_coords[0]

    for lat, lon in decoded_coords[1:-1]:
        if haversine_distance(last_lat, last_lon, lat, lon) >= min_distance_miles:
            selected.append((lat, lon))
            last_lat, last_lon = lat, lon
            if len(selected) >= max_samples - 1:
                break

    selected.append(decoded_coords[-1])
    return selected[:max_samples]




if json_file_path.exists():
    try:
        with open(json_file_path, 'r') as f:
            user_nmfc_data = json.load(f)
    except json.JSONDecodeError:
        user_nmfc_data = []
else:
    user_nmfc_data = []

def convert_user_nmfc_data_to_dict(user_data):
    converted = {}
    for item in user_data:
        description = item.get("description")
        nmfc = item.get("nmfc")
        density_based = item.get("density_based", False)
        class_logic = item.get("class_logic")
        density_map = item.get("density_map", [])
        weight_map = item.get("weight_map", [])
        value_map = item.get("value_map", [])
        fixed_class = item.get("class")
        sub_code = item.get("sub_code", "")

        if density_based:
            converted[description] = {
                "nmfc": nmfc,
                "density_based": True,
                "density_map": density_map
            }
        elif class_logic == "weight_map":
            converted[description] = {
                "nmfc": nmfc,
                "density_based": False,
                "class_logic": "per_item_weight",
                "class_map": weight_map
            }
        elif class_logic == "value_map":
            converted[description] = {
                "nmfc": nmfc,
                "density_based": False,
                "class_logic": "per_value",
                "class_map": value_map
            }
        elif class_logic == "fixed":
            converted[description] = {
                "nmfc": nmfc,
                "density_based": False,
                "class_logic": "fixed",
                "class": fixed_class,
                "sub_code": sub_code
            }

    return converted


user_freight_class_table = convert_user_nmfc_data_to_dict(user_nmfc_data)

all_freight_classes = dict(FREIGHT_CLASS_TABLE)




GOOGLE_MAPS_API_KEY = """REPLACE_ME"""
DEFAULT_UNLOAD_TIME_HOURS = 1.0
DEFAULT_DETENTION_RATE = 50.0
DEFAULT_AVERAGE_MPH = 45
LOGO_BASE64 = """REPLACE_ME"""
ICON_BASE64 = """REPLACE_ME"""


def setup_checkbutton_styles():
    style = ttk.Style()
    style.theme_use('default')

    style.configure("Custom.TCheckbutton",
        background=get_theme_colors()["bg"],
        foreground=get_theme_colors()["fg"],
        font=("Segoe UI", 10),
        indicatorcolor='white',  # Doesn't affect all platforms, but helps
        indicatordiameter=10,
        padding=5
    )

    style.map("Custom.TCheckbutton",
        background=[('active', get_theme_colors()["bg"])],
        foreground=[('active', get_theme_colors()["fg"])],
        indicatorcolor=[('selected', 'white')],
    )


_temp_icon_path = None

# Decodes a base64 string into a temporary .ico file and returns its path.
# Used for branding the GUI window or EXE.
def get_temp_icon_path():
    global _temp_icon_path
    if _temp_icon_path is None:
        icon_data = base64.b64decode(ICON_BASE64)
        _temp_icon_path = os.path.join(tempfile.gettempdir(), 'nal_temp_icon.ico')
        with open(_temp_icon_path, 'wb') as icon_file:
            icon_file.write(icon_data)
    return _temp_icon_path

@atexit.register
def cleanup_temp_icon():
    global _temp_icon_path
    if _temp_icon_path and os.path.exists(_temp_icon_path):
        try:
            os.remove(_temp_icon_path)
            print("🧹 Temp icon removed.")
        except Exception:
            pass


def create_toplevel_window(root):
    win = tk.Toplevel(root)
    try:
        win.iconbitmap(get_temp_icon_path())
    except Exception as e:
        print("⚠️ Could not set icon:", e)
    try:
        apply_theme(win)
        apply_ttk_theme()
    except Exception as e:
        print("⚠️ Could not apply theme:", e)
    return win

def get_theme_colors():
    default_theme = "Light Mode"
    theme_options = {
        "Light Mode": {"bg": "white", "fg": "black"},
        "Dark Mode": {"bg": "#202020", "fg": "white"},
        "Slate Gray": {"bg": "darkgray", "fg": "black"},
        "Midnight Blue": {"bg": "#191970", "fg": "white"},
        "Forest Green": {"bg": "#228B22", "fg": "white"},
        "Royal Purple": {"bg": "#6A0DAD", "fg": "white"},
        "Steel Blue": {"bg": "#4682B4", "fg": "white"},
        "Desert Tan": {"bg": "#D2B48C", "fg": "black"},
        "Sky Blue": {"bg": "#87CEEB", "fg": "black"},
        "Crimson": {"bg": "#DC143C", "fg": "white"},
        "Coral Sunset": {"bg": "#FF6F61", "fg": "white"},
        "Cool Teal": {"bg": "#008080", "fg": "white"},
        "Sunburst Orange": {"bg": "#FFA500", "fg": "#2E1A00"},
        "Neon Green": {"bg": "#39FF14", "fg": "#000000"},
        "Hot Pink Punch": {"bg": "#FF69B4", "fg": "#2F004F"},
        "Aqua Splash": {"bg": "#00FFFF", "fg": "#004040"},
        "Mint Cream": {"bg": "#F5FFFA", "fg": "#003366"},
        "Pastel Peach": {"bg": "#FFDAB9", "fg": "#5C4033"},
        "Lavender Mist": {"bg": "#E6E6FA", "fg": "#4B0082"},
        "Soft Lilac": {"bg": "#D8BFD8", "fg": "#333333"},
        "Powder Blue": {"bg": "#B0E0E6", "fg": "#003366"},
        "Wheat Beige": {"bg": "#F5DEB3", "fg": "#3C2F2F"},
        "Charcoal Glow": {"bg": "#36454F", "fg": "#FFD700"},
        "High Contrast": {"bg": "#000000", "fg": "#FFFF00"},
        "Obsidian": {"bg": "#0B0C10", "fg": "#C5C6C7"},
        "Graphite": {"bg": "#2F4F4F", "fg": "#F8F8FF"},
        "Deep Sea Blue": {"bg": "#001F3F", "fg": "#7FDBFF"},
    }

    try:
        config_path = os.path.join(os.path.expanduser("~"), "Documents", "Transit Time Calculator", "eta_config.json")
        if os.path.exists(config_path):
            with open(config_path, "r") as f:
                config = json.load(f)
                selected_theme = config.get("selected_theme", default_theme)
                return theme_options.get(selected_theme, theme_options[default_theme])
    except:
        pass

    return theme_options[default_theme]

def apply_theme(widget):
    colors = get_theme_colors()
    bg, fg = colors["bg"], colors["fg"]

    try:
        widget.configure(bg=bg, fg=fg)
    except Exception:
        try:
            widget.configure(bg=bg)
        except:
            pass

    for child in widget.winfo_children():
        try:
            if isinstance(child, tk.Entry):
                child.configure(
                    bg=bg,
                    fg=fg,
                    insertbackground=fg,
                    readonlybackground=bg  # <- fixes hidden readonly fields
                )
            elif isinstance(child, (tk.Label, tk.Button, tk.Text)):
                child.configure(bg=bg, fg=fg, insertbackground=fg)
            elif isinstance(child, (tk.Checkbutton, tk.Radiobutton)):
                child.configure(
                    bg=bg,
                    fg=fg,
                    activebackground=bg,
                    activeforeground=fg,
                    selectcolor=bg
                )
            elif isinstance(child, (tk.Frame, tk.Canvas)):
                child.configure(bg=bg)
            elif isinstance(child, tk.OptionMenu):
                child.configure(bg=bg, fg=fg)
                child["menu"].configure(bg=bg, fg=fg)
        except:
            pass

        apply_theme(child)




def apply_ttk_theme():
    colors = get_theme_colors()
    bg, fg = colors["bg"], colors["fg"]

    style = ttk.Style()
    try:
        style.theme_use("default")
    except:
        pass

    style.configure("TLabel", background=bg, foreground=fg)
    style.configure("TButton", background=bg, foreground=fg)
    style.configure("TCheckbutton", background=bg, foreground=fg)
    style.configure("TRadiobutton", background=bg, foreground=fg)
    style.configure("TEntry", fieldbackground=bg, background=bg, foreground=fg)
    style.configure("TCombobox", fieldbackground=bg, background=bg, foreground=fg)
    style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg)

    style.map("TButton",
              background=[("active", bg)],
              foreground=[("active", fg)])

_original_toplevel = tk.Toplevel

def patched_toplevel(*args, **kwargs):
    win = _original_toplevel(*args, **kwargs)
    try:
        win.iconbitmap(get_temp_icon_path())
    except Exception as e:
        print("⚠️ Could not set icon:", e)
    try:
        apply_theme(win)
    except Exception as e:
        print("⚠️ Could not apply theme:", e)
    return win

tk.Toplevel = patched_toplevel


root = tk.Tk()
root.title('ETA Calculator')
icon_data = base64.b64decode(ICON_BASE64)
temp_icon_path = os.path.join(tempfile.gettempdir(), 'nal_temp_icon.ico')
with open(temp_icon_path, 'wb') as icon_file:
    icon_file.write(icon_data)
root.iconbitmap(temp_icon_path)
logo_data = base64.b64decode(LOGO_BASE64)
logo_image = Image.open(io.BytesIO(logo_data))
logo_tk = ImageTk.PhotoImage(logo_image)
logo_label = tk.Label(root, image=logo_tk)
logo_label.grid(row=0, column=0, columnspan=4, pady=(10, 5))
advanced_mode = tk.BooleanVar()
planning_by_arrival = tk.BooleanVar()
waypoint_entries = []
delivery_time_entries = []


def decode_polyline(polyline_str):
    try:
        index, lat, lng = 0, 0, 0
        coordinates = []

        while index < len(polyline_str):
            shift, result = 0, 0
            while True:
                b = ord(polyline_str[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            dlat = ~(result >> 1) if (result & 1) else (result >> 1)
            lat += dlat

            shift, result = 0, 0
            while True:
                b = ord(polyline_str[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            dlng = ~(result >> 1) if (result & 1) else (result >> 1)
            lng += dlng

            coordinates.append((lat / 1e5, lng / 1e5))

        log_info(f"Decoded polyline to {len(coordinates)} coordinates.")
        return coordinates

    except Exception as e:
        log_error(f"Failed to decode polyline: {e}")
        return []




def get_states_from_leg(leg):
    states = set()
    try:
        end_address = leg.get("end_address", "")
        match = re.search(r',\s*([A-Z]{2})\s+\d{5}', end_address)
        if match:
            states.add(match.group(1))
        else:
            fallback_match = re.search(r',\s*([A-Z]{2})\b', end_address)
            if fallback_match:
                states.add(fallback_match.group(1))
        log_info(f"Extracted states from leg: {states}")
    except Exception as e:
        log_error(f"Error extracting state from leg: {e}")
    return states




    

def get_state_abbr_from_location(location_string):
    match = re.search(r',\s*([A-Z]{2})\b', location_string.upper())
    if match:
        log_info(f"Matched state abbreviation: {match.group(1)}")
        return match.group(1)
    return ""




def toggle_advanced():
    try:
        if advanced_mode.get():
            add_waypoint_button.grid(row=15, column=0, columnspan=2, sticky='w', padx=5)
            log_info("Advanced Mode enabled.")
        else:
            add_waypoint_button.grid_remove()
            clear_waypoints()
            log_info("Advanced Mode disabled.")
    except Exception as e:
        log_error(f"Error toggling advanced mode: {e}")



def toggle_arrival_mode():

    if planning_by_arrival.get():
        label_time.config(text='Arrival Time (MM/DD/YYYY HH:MM AM/PM):')
    else:
        label_time.config(text='Departure Time (MM/DD/YYYY HH:MM AM/PM):')
        
        
        
tk.Label(root, text='Shipment Parameters', font=('Arial', 10, 'bold')).grid(row=1, column=0, columnspan=2, sticky='w', padx=5, pady=(10, 0))
tk.Checkbutton(root, text='Enable Advanced Options', variable=advanced_mode, command=toggle_advanced).grid(row=2, column=0, sticky='w', padx=5)
labels = ['Total Miles:', 'Average Speed (mph):', 'Max Drive Hours:', 'Break Hours:', 'Origin Address:', 'Destination Address:']
defaults = ['', '45', '11', '10', 'Detroit, MI', 'Dallas, TX']
entries = []
for i, (label, default) in enumerate(zip(labels, defaults)):
    tk.Label(root, text=label).grid(row=i + 3, column=0, sticky='e', padx=5, pady=2)
    entry = tk.Entry(root, width=40)
    entry.insert(0, default)
    entry.grid(row=i + 3, column=1, padx=5, pady=2)
    entries.append(entry)
entry_miles, entry_speed, entry_drive_hours, entry_break_hours, entry_origin, entry_destination = entries
label_time = tk.Label(root, text='Departure Time (MM/DD/YYYY HH:MM AM/PM):')
label_time.grid(row=9, column=0, sticky='e', padx=5, pady=2)
entry_datetime = tk.Entry(root, width=30)
entry_datetime.insert(0, datetime.now().strftime('%m/%d/%Y %I:%M %p'))
entry_datetime.grid(row=9, column=1, padx=5, pady=2, sticky='w')
toggle_btn = ttk.Checkbutton(root, text='Plan by Arrival', variable=planning_by_arrival, command=toggle_arrival_mode)
toggle_btn.grid(row=9, column=2, padx=10, sticky='w')
tk.Label(root, text='ETA Calculations:', font=('Arial', 10, 'bold')).grid(row=10, column=0, columnspan=2, sticky='w', padx=5, pady=(10, 0))
tk.Label(root, text='Use the buttons below to calculate the estimated arrival time.').grid(row=11, column=0, columnspan=3, sticky='w', padx=5)


def copy_to_clipboard():
    try:
        result_text = output_box.get("1.0", tk.END).strip()
        if result_text:
            root.clipboard_clear()
            root.clipboard_append(result_text)
            root.update()
            log_info("Output copied to clipboard.")
        else:
            messagebox.showinfo("Copy to Clipboard", "Nothing to copy.")
            log_info("Copy to clipboard attempted with no output.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to copy result:\n{e}")
        log_error(f"Failed to copy to clipboard: {e}")

        


# Converts raw user NMFC entries into a dictionary keyed by description.
# Each entry includes NMFC code and logic type (density-based, weight, etc.)

def convert_user_nmfc_data_to_dict(user_data):
    converted = {}
    log_info("🔄 Starting NMFC user data conversion")

    for item in user_data:
        try:
            description = item.get("description")
            nmfc = item.get("nmfc")
            density_based = item.get("density_based", False)
            class_logic = item.get("class_logic")
            density_map = item.get("density_map", [])
            weight_map = item.get("weight_map", [])
            value_map = item.get("value_map", [])
            fixed_class = item.get("class")
            sub_code = item.get("sub_code", "")

            if not description or not nmfc:
                log_warning(f"⚠️ Skipping NMFC entry with missing description or NMFC: {item}")
                continue

            if density_based:
                converted[description] = {
                    "nmfc": nmfc,
                    "density_based": True,
                    "density_map": density_map
                }
                log_debug(f"✅ Loaded Density-Based NMFC: {description} ({nmfc})")
            elif class_logic == "weight_map":
                converted[description] = {
                    "nmfc": nmfc,
                    "density_based": False,
                    "class_logic": "per_item_weight",
                    "class_map": weight_map
                }
                log_debug(f"✅ Loaded Weight-Based NMFC: {description} ({nmfc})")
            elif class_logic == "value_map":
                converted[description] = {
                    "nmfc": nmfc,
                    "density_based": False,
                    "class_logic": "per_value",
                    "class_map": value_map
                }
                log_debug(f"✅ Loaded Value-Based NMFC: {description} ({nmfc})")
            elif class_logic == "fixed":
                converted[description] = {
                    "nmfc": nmfc,
                    "density_based": False,
                    "class_logic": "fixed",
                    "class": fixed_class,
                    "sub_code": sub_code
                }
                log_debug(f"✅ Loaded Fixed-Class NMFC: {description} ({nmfc})")
            else:
                log_warning(f"⚠️ Skipped NMFC entry with unknown class_logic: {description} ({nmfc})")

        except Exception as e:
            log_error(f"❌ Error processing NMFC entry: {item}\n{e}")

    log_info(f"✅ Conversion complete. {len(converted)} freight types loaded.")
    return converted





# Opens a popup GUI allowing users to define new NMFC freight types,
# supporting density, weight, value, or fixed class logic.
def open_add_freight_type():
    import json
    import os
    from pathlib import Path
    from tkinter import Toplevel, Label, Entry, Button, StringVar, OptionMenu, Frame, Scrollbar, Canvas, BOTH, LEFT, RIGHT, VERTICAL, Y, messagebox

    log_info("Opening 'Add NMFC Freight Type' wizard")

    documents_path = Path.home() / "Documents" / "Transit Time Calculator"
    json_file_path = documents_path / "user_nmfc_data.json"
    os.makedirs(documents_path, exist_ok=True)

    if json_file_path.exists():
        try:
            with open(json_file_path, 'r') as f:
                user_nmfc_data = json.load(f)
            log_info("Loaded existing NMFC user data")
        except json.JSONDecodeError:
            log_error("Failed to decode existing NMFC JSON. Starting with empty list.")
            user_nmfc_data = []
    else:
        user_nmfc_data = []
        log_info("No existing NMFC JSON found. Starting with empty list.")

    wizard = create_toplevel_window(tk._default_root)
    wizard.title("➕ Add NMFC Freight Type")
    wizard.geometry("520x600")

    subcode_entries = []
    selected_logic = StringVar()
    selected_logic.set("Density-Based")

    Label(wizard, text="Step 1: Description").pack()
    desc_entry = Entry(wizard)
    desc_entry.pack()

    Label(wizard, text="Step 2: NMFC Code").pack()
    nmfc_entry = Entry(wizard)
    nmfc_entry.pack()

    Label(wizard, text="Step 3: Select Classification Type").pack()
    OptionMenu(wizard, selected_logic, "Density-Based", "Weight-Based", "Cost-Based", "Fixed Class").pack()

    def next_step():
        log_info(f"Next step triggered for logic type: {selected_logic.get()}")
        for widget in wizard.winfo_children():
            if isinstance(widget, Frame) or isinstance(widget, Canvas):
                widget.destroy()

        logic = selected_logic.get()
        logic_type = {
            "Density-Based": "density_map",
            "Weight-Based": "weight_map",
            "Cost-Based": "value_map",
            "Fixed Class": "fixed"
        }[logic]

        Label(wizard, text=f"Step 4: Define Subcodes ({logic})").pack()

        if logic == "Fixed Class":
            Label(wizard, text="Enter Fixed Class:").pack()
            fixed_class_entry = Entry(wizard)
            fixed_class_entry.pack(pady=5)

            Label(wizard, text="Optional Sub Code:").pack()
            fixed_subcode_entry = Entry(wizard)
            fixed_subcode_entry.pack(pady=5)
        else:
            frame = Frame(wizard)
            frame.pack(pady=10, fill=BOTH, expand=True)

            canvas = Canvas(frame, borderwidth=0)
            canvas.pack(side=LEFT, fill=BOTH, expand=True)

            scrollbar = Scrollbar(frame, orient=VERTICAL, command=canvas.yview)
            scrollbar.pack(side=RIGHT, fill=Y)
            canvas.configure(yscrollcommand=scrollbar.set)

            inner_frame = Frame(canvas)
            canvas.create_window((0, 0), window=inner_frame, anchor="nw")

            def on_configure(event):
                canvas.configure(scrollregion=canvas.bbox("all"))
            inner_frame.bind("<Configure>", on_configure)

            subcode_entries.clear()

            for i in range(8):
                row = Frame(inner_frame)
                row.pack(pady=2, anchor="w")

                Label(row, text="Threshold:").pack(side=LEFT)
                threshold = Entry(row, width=6)
                threshold.pack(side=LEFT, padx=2)

                Label(row, text="Class:").pack(side=LEFT)
                class_entry = Entry(row, width=10)
                class_entry.pack(side=LEFT, padx=2)

                Label(row, text="Sub Code:").pack(side=LEFT)
                subcode = Entry(row, width=12)
                subcode.pack(side=LEFT, padx=2)

                subcode_entries.append((threshold, class_entry, subcode))

        def save_nmfc():
            nonlocal user_nmfc_data
            log_info("Attempting to save new NMFC type")

            if logic == "Fixed Class":
                class_val = fixed_class_entry.get().strip()
                sub_val = fixed_subcode_entry.get().strip()
                if not desc_entry.get().strip() or not nmfc_entry.get().strip() or not class_val:
                    log_error("Missing required fixed class fields")
                    messagebox.showerror("Missing Info", "All fields must be filled out properly.")
                    return
                data = {
                    "description": desc_entry.get().strip(),
                    "nmfc": nmfc_entry.get().strip(),
                    "density_based": False,
                    "class_logic": "fixed",
                    "class": class_val,
                    "sub_code": sub_val
                }
            else:
                data = {
                    "description": desc_entry.get().strip(),
                    "nmfc": nmfc_entry.get().strip(),
                    "density_based": logic == "Density-Based",
                    "class_logic": None if logic == "Density-Based" else logic_type,
                    logic_type: []
                }

                for thresh, cls, sub in subcode_entries:
                    try:
                        thresh_val = float(thresh.get())
                        cls_val = cls.get().strip()
                        sub_val = sub.get().strip()
                        if cls_val:
                            data[logic_type].append((thresh_val, cls_val, sub_val))
                    except ValueError:
                        continue

                if not data["description"] or not data["nmfc"] or not data[logic_type]:
                    log_error("Missing required density/weight/value fields")
                    messagebox.showerror("Missing Info", "All fields must be filled out properly.")
                    return

            user_nmfc_data.append(data)
            try:
                with open(json_file_path, "w") as f:
                    json.dump(user_nmfc_data, f, indent=2)
                log_info(f"Saved NMFC type: {data['description']}")
            except Exception as e:
                log_error(f"Failed to save NMFC data: {e}")
                messagebox.showerror("Save Failed", f"Could not save data:\n{e}")
                return

            global user_freight_class_table, all_freight_classes, FREIGHT_CLASS_TABLE
            user_freight_class_table = convert_user_nmfc_data_to_dict(user_nmfc_data)
            all_freight_classes = dict(FREIGHT_CLASS_TABLE)
            all_freight_classes.update(user_freight_class_table)

            if callable(refresh_dropdown_global):
                log_info("Refreshing dropdown options after save")
                refresh_dropdown_global()

            messagebox.showinfo("Saved", "✅ NMFC Freight Type saved to database!")
            wizard.destroy()

        Button(wizard, text="💾 Save to NMFC JSON", command=save_nmfc).pack(pady=10)

    Button(wizard, text="➡️ Next", command=next_step).pack(pady=10)
    apply_theme(wizard)




def bring_density_to_front():
    try:
        density_calculator_window.lift()
        density_calculator_window.attributes("-topmost", True)
        density_calculator_window.after(100, lambda: density_calculator_window.attributes("-topmost", False))
        density_calculator_window.focus_force()
    except:
        pass



# Opens the LTL density calculator GUI.
# Allows pallet-by-pallet entry and calculates class, linear feet, and overlength violations.

def open_density_calculator():
    log_info("📦 open_density_calculator() called")

    import tkinter as tk
    from tkinter import messagebox
    import json
    from pathlib import Path
    from collections import defaultdict

    def estimate_freight_class(density):
        log_debug(f"Estimating freight class for density: {density:.2f}")
        if density >= 50: return "Class 50"
        elif density >= 35: return "Class 55"
        elif density >= 30: return "Class 60"
        elif density >= 22.5: return "Class 65"
        elif density >= 15: return "Class 70"
        elif density >= 13.5: return "Class 77.5"
        elif density >= 12: return "Class 85"
        elif density >= 10: return "Class 92.5"
        elif density >= 9: return "Class 100"
        elif density >= 8: return "Class 110"
        elif density >= 7: return "Class 125"
        elif density >= 6: return "Class 150"
        elif density >= 5: return "Class 175"
        elif density >= 4: return "Class 200"
        elif density >= 3: return "Class 250"
        elif density >= 2: return "Class 300"
        else: return "Class 400-500"

    def get_density_based_class(density, density_map):
        log_debug("Using density-based class lookup")
        for threshold, freight_class, sub_code in density_map:
            if density < threshold:
                return freight_class, sub_code
        return density_map[-1][1], density_map[-1][2]

# Estimates total linear footage required based on pallet width and trailer layout.
# Simulates side-by-side placement (row fitting) using trailer width constraints (e.g. 98 inches).
# Adds pallet lengths together in rows and totals the depth used.    
    
    def calculate_ltl_linear_feet_from_entries(pallet_rows, trailer_width_in=98):
        log_debug("Calculating layout-based LTL linear feet")
        total_rows = 0
        row_width_remaining = trailer_width_in
        current_row_depth = 0
        total_depth_in = 0
        all_pallet_lengths_ft = []

        for pallet in pallet_rows:
            try:
                length_in = float(pallet["entries"][0].get())
                width_in = float(pallet["entries"][1].get())
                quantity = int(pallet["entries"][4].get())
            except Exception as e:
                log_error(f"Invalid pallet input: {e}")
                continue

            for _ in range(quantity):
                if width_in > row_width_remaining:
                    total_rows += 1
                    total_depth_in += current_row_depth
                    row_width_remaining = trailer_width_in
                    current_row_depth = 0

                row_width_remaining -= width_in
                current_row_depth = max(current_row_depth, length_in)
                all_pallet_lengths_ft.append(length_in / 12)

        total_depth_in += current_row_depth
        linear_feet = total_depth_in / 12
        log_info(f"📏 Total linear feet: {linear_feet:.2f}")
        log_debug(f"Pallet lengths (ft): {all_pallet_lengths_ft}")
        return linear_feet, all_pallet_lengths_ft

    log_info("🔧 Initializing GUI window")
    global density_calculator_window
    density_calculator_window = tk.Toplevel()
    window = density_calculator_window
    window.title("📦 LTL Density Calculator")
    window.geometry("900x850")
    window.lift()
    window.attributes("-topmost", True)
    window.after(100, lambda: window.attributes("-topmost", False))
    window.focus_force()

    canvas = tk.Canvas(window)
    scrollbar = tk.Scrollbar(window, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=scrollbar.set)
    scrollable_frame = tk.Frame(canvas)
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
    scrollbar.pack(side="right", fill="y", padx=(0, 10))

    header = tk.Frame(scrollable_frame)
    header.grid(row=0, column=0, sticky="w")
    for idx, text in enumerate(["Length (in)", "Width (in)", "Height (in)", "Weight (lbs)", "Quantity"]):
        tk.Label(header, text=text, width=10).grid(row=0, column=idx, padx=2)
    tk.Label(header, text="", width=10).grid(row=0, column=5)

    pallet_rows = []
    warning_label = None
    overlength_label = None

    def add_pallet_row():
        log_info("➕ Adding new pallet row")
        row_index = len(pallet_rows) + 1
        bg_color = "white" if row_index % 2 == 1 else window.cget("background")
        row = tk.Frame(scrollable_frame, bg=bg_color)
        row.grid(row=row_index, column=0, sticky="w", pady=1)
        entries = []
        for i in range(5):
            e = tk.Entry(row, width=12, justify="center")
            e.grid(row=0, column=i, padx=2, pady=2)
            entries.append(e)
        tk.Button(row, text="Delete", command=lambda r=row: delete_row(r)).grid(row=0, column=5, padx=2)
        pallet_rows.append({"frame": row, "entries": entries})
        apply_theme(row)

    def delete_row(row):
        log_info("🗑️ Deleting a pallet row")
        for i, p in enumerate(pallet_rows):
            if p["frame"] == row:
                pallet_rows.pop(i)
                break
        row.destroy()

    tk.Button(window, text="➕ Add Pallet", command=add_pallet_row).pack(pady=10)

    nmfc_options = ["Select NMFC Description"]
    selected_nmfc = tk.StringVar(window)
    selected_nmfc.set(nmfc_options[0])

    user_freight_class_table = {}
    try:
        log_info("📂 Loading user NMFC data")
        path = Path.home() / "Documents/Transit Time Calculator/user_nmfc_data.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                user_nmfc_data = json.load(f)
                user_freight_class_table = convert_user_nmfc_data_to_dict(user_nmfc_data)
    except Exception as e:
        log_error(f"Error loading user NMFC data: {e}")

    all_freight_classes = dict(FREIGHT_CLASS_TABLE)
    all_freight_classes.update(user_freight_class_table)

    for desc in sorted(all_freight_classes.keys()):
        nmfc_options.append(desc)
    tk.OptionMenu(window, selected_nmfc, *nmfc_options).pack(pady=(0, 10))

    result_label = tk.Label(window, text="", font=("Helvetica", 12), pady=10)
    result_label.pack()

    def calculate_density():
        log_info("🧮 Running density calculation")
        nonlocal warning_label, overlength_label
        total_weight = 0
        total_cubic_inches = 0
        pallet_lengths_ft = []

        for row in pallet_rows:
            try:
                l, w, h, wt, qty = [float(e.get()) if i != 4 else int(e.get()) for i, e in enumerate(row["entries"])]
                total_weight += wt
                total_cubic_inches += (l * w * h) * qty
                pallet_lengths_ft.extend([l / 12] * qty)
            except Exception as e:
                log_warning(f"Skipping row due to error: {e}")
                continue

        if total_cubic_inches == 0:
            log_error("Volume cannot be zero. Showing error to user.")
            return messagebox.showerror("Error", "Volume cannot be zero.")

        density = total_weight / (total_cubic_inches / 1728)
        log_info(f"📦 Density: {density:.2f} lbs/ft³")
        selected = selected_nmfc.get()
        log_debug(f"NMFC selected: {selected}")
        info = all_freight_classes.get(selected)
        text = f"📦 Density: {density:.2f} lbs/ft³\n"

        final_class = None
        if not info or selected == "Select NMFC Description":
            final_class = estimate_freight_class(density)
            text += f"Estimated Freight Class: {final_class}"
        elif info.get("density_based"):
            final_class, sub = get_density_based_class(density, info["density_map"])
            text += f"Class: {final_class}\nNMFC: {info['nmfc']}\nSub Code: {sub}"
        elif info.get("class_logic") == "per_item_weight":
            pcs = sum(int(r["entries"][4].get()) for r in pallet_rows if all(e.get() for e in r["entries"]))
            each = total_weight / pcs if pcs else 0
            for limit, cls, sub in info["class_map"]:
                if each < limit:
                    final_class = cls
                    text += f"Each Item: {each:.2f} lbs\nClass: {cls}\nNMFC: {info['nmfc']}\nSub Code: {sub}"
                    break
        else:
            final_class = info.get("class")
            text += f"Class: {final_class}\nNMFC: {info.get('nmfc')}\nSub Code: {info.get('sub_code', 'N/A')}"

        result_label.config(text=text)

        if warning_label:
            warning_label.destroy()

        if final_class in ["Class 50", "Class 55"]:
            log_warning(f"Low freight class warning triggered: {final_class}")
            warning_label = tk.Label(
                window,
                text="⚠️ Class is very low. Please confirm NMFC or default to Class 60 if unsure/unavailable.",
                fg="red",
                font=("Arial", 10, "bold"),
                justify="center",
                wraplength=250
            )
            warning_label.pack(pady=5)

            def blink_warning():
                if warning_label and warning_label.winfo_exists():
                    current = warning_label.cget("fg")
                    warning_label.config(fg="red" if current == "white" else "white")
                    window.after(500, blink_warning)

            blink_warning()

        # Overlength logic
        ltl_linear_feet, pallet_lengths_ft = calculate_ltl_linear_feet_from_entries(pallet_rows)
        overlength_rules = [
    {
        "carriers": ["AAA Cooper"],
        "item_limits": [(8, "Pallet ≥ 8 ft"), (12, "Pallet ≥ 12 ft"), (16, "Pallet ≥ 16 ft"), (20, "Pallet ≥ 20 ft")],
        "shipment_limit_ft": 12
    },
    {
        "carriers": ["ABF"],
        "item_limits": [(12, "Pallet ≥ 12 ft")],
        "shipment_limit_ft": 30
    },
    {
        "carriers": ["Dayton"],
        "item_limits": [(7, "Pallet ≥ 7 ft"), (10, "Pallet ≥ 10 ft"), (12, "Pallet ≥ 12 ft"), (14, "Pallet ≥ 14 ft")],
        "shipment_limit_ft": 15
    },
    {
        "carriers": ["Old Dominion"],
        "item_limits": [(8, "Pallet ≥ 8 ft")],
        "shipment_limit_ft": 20
    },
    {
        "carriers": ["Saia"],
        "item_limits": [(8, "Pallet ≥ 8 ft"), (12, "Pallet ≥ 12 ft")],
        "shipment_limit_ft": 30
    },
    {
        "carriers": ["XPO"],
        "item_limits": [(8, "Pallet ≥ 8 ft"), (11, "Pallet ≥ 11 ft"), (16, "Pallet ≥ 16 ft")],
        "shipment_limit_ft": 28
    },
    {
        "carriers": ["FedEx Freight", "Estes"],
        "item_limits": [(8, "Pallet ≥ 8 ft")],
        "shipment_limit_ft": 30
    }
]

        carrier_item_hits = defaultdict(list)
        carrier_shipment_hits = {}

        for rule in overlength_rules:
            item_limits = rule.get("item_limits", [])
            shipment_limit = rule.get("shipment_limit_ft", float("inf"))

            for carrier in rule["carriers"]:
                for limit_ft, label in item_limits:
                    if any(p >= limit_ft for p in pallet_lengths_ft):
                        log_debug(f"{carrier} matches item threshold: {label}")
                        carrier_item_hits[carrier].append((limit_ft, label))

                if ltl_linear_feet >= shipment_limit:
                    log_debug(f"{carrier} matches shipment threshold: Shipment ≥ {shipment_limit} ft")
                    carrier_shipment_hits[carrier] = (shipment_limit, f"Shipment ≥ {shipment_limit} ft")

        grouped_alerts = defaultdict(set)
        for carrier, hits in carrier_item_hits.items():
            if hits:
                top = max(hits, key=lambda x: x[0])
                log_info(f"{carrier} final item alert: {top[1]}")
                grouped_alerts[top[1]].add(carrier)

        for carrier, (_, label) in carrier_shipment_hits.items():
            log_info(f"{carrier} final shipment alert: {label}")
            grouped_alerts[label].add(carrier)

        if overlength_label:
            overlength_label.destroy()

        if grouped_alerts:
            alert_lines = []
            for label, carriers in sorted(grouped_alerts.items()):
                carrier_line = ", ".join(sorted(carriers))
                alert_lines.append(f"⚠️ {label}\nCarriers: {carrier_line}")

            overlength_label = tk.Label(window, text="\n\n".join(alert_lines), fg="black", bg="white",
                                        font=("Arial", 10, "bold"), justify="center", wraplength=500)
            overlength_label.pack(pady=5)

            def blink_overlength():
                if overlength_label and overlength_label.winfo_exists():
                    bg = overlength_label.cget("bg")
                    overlength_label.config(bg="orange" if bg == "white" else "white")
                    window.after(500, blink_overlength)

            blink_overlength()

    tk.Button(window, text="🧮 Calculate Density", command=calculate_density).pack(pady=10)
    tk.Button(window, text="Need help finding your NMFC? Contact us.", command=contact_help).pack(pady=5)
    tk.Button(window, text="➕ Add NMFC Freight Type", command=open_add_freight_type).pack(pady=5)
    apply_theme(window)
    log_info("🎨 Theme applied to window")















def contact_help():
    subject = "NMFC Code Request"
    body = (
        "Hi,\n\n"
        "I need help finding the correct NMFC code for a shipment. Here are the shipment details:\n\n"
        "- Description of goods:\n"
        "- What is the product made of?\n"
        "- Total weight (lbs):\n"
        "- Dimensions (L x W x H in inches):\n"
        "- Piece count:\n"
        "- Is it stackable or fragile?\n"
        "- Is it boxed, palletized, or loose?\n"
        "- Any additional info that might help:\n\n"
        "Thanks!"
    )
    mailto_url = f"mailto:REPLACE_ME?subject={urllib.parse.quote(subject)}&body={urllib.parse.quote(body)}"
    log_info("📧 Opening NMFC help email template")
    webbrowser.open(mailto_url)


def open_help_window():
    help_win = create_toplevel_window(root)
    help_win.title("Help - ETA Calculator")
    help_win.geometry("600x800")
    help_win.transient(root)
    help_win.grab_set()

    log_info("📖 Help window opened")

    text_widget = tk.Text(help_win, wrap=tk.WORD, font=("Helvetica", 11))
    text_widget.pack(expand=True, fill="both", padx=10, pady=10)
    text_widget.tag_configure("bold", font=("Helvetica", 11, "bold"))
    text_widget.tag_configure("title", font=("Helvetica", 14, "bold"), justify="center")
    text_widget.tag_configure("link", foreground="blue")

    text_widget.insert(tk.END, "Welcome to the ETA Calculator!\n", "title")
    text_widget.insert(tk.END, "\nHere’s how to use it:\n\n")

    sections = [
        ("1. Enter Pickup & Delivery Info", "- Type in the pickup and delivery locations.\n- Enter a departure or arrival time and select the mode.\n"),
        ("2. Set Break Hours (if needed)", "- Optional: Add break time to account for driver rest or delays.\n"),
        ("3. Smart ETA Output", "- Uses Google Maps real-time traffic data to calculate the most accurate ETA possible.\n- Unload time is added to each stop for multi-stop routes.\n- Adjusts ETA for traffic delays or faster-than-usual routes.\n- Checks for weather alerts along the route using the National Weather Service.\n- Provides smart equipment and planning suggestions if Smart Recommendations are enabled.\n\n💡 Smart ETA helps make informed planning decisions based on traffic, routing, HOS, and weather conditions.\n"),
        ("4. Calculate ETA (No Traffic)", "- Enter total miles to get a rough ETA using shift length and average speed.\n- Great for general planning or long-haul estimates.\n"),
        ("5. Advanced Mode (Multi-Stop)", "- Switches to multi-stop planning view.\n- Input each stop in order, including unloading time and break hours.\n- Calculates stop-by-stop arrival times based on Smart ETA.\n"),
        ("6. LTL Density Calculator 📦", "- Opens a window to calculate freight class based on weight and dimensions.\n- Select from common freight types or enter custom details.\n- Displays density, estimated class, and NMFC codes with sub codes.\n"),
        ("7. Add NMFC Freight Type ➕", "- Use the 'Add NMFC Freight Type' button to create your own freight types.\n- Choose Density-Based, Weight-Based, or Value-Based classification.\n- Entries are saved and will appear in the calculator dropdown on restart.\n"),
        ("8. Settings ⚙️", "- Customize default origin, destination, unload time, detention rate, and theme.\n- Toggle Smart Recommendations for additional route planning tips.\n- Preferences are saved between sessions.\n"),
        ("9. Detention Calculator", "- Enter arrival and load times.\n- Calculates detention owed after 2 free hours in 15-minute increments.\n"),
        ("10. Linear Feet Calculator 📏", "- Estimate total linear feet required for mixed pallet loads.\n- Add multiple pallets with dimensions and stackability info.\n- Get layout and equipment upgrade suggestions.\n"),
        ("11. View Layout 👁", "- After calculating linear feet, click this button to see a top-down trailer view.\n- Shows how pallets may be arranged by width and depth.\n- Works with stackable and rotatable pallets.\n"),
        ("12. Need help finding an NMFC code?", "- Use the 'Need help finding your NMFC?' button.\n- It opens your email client with a pre-filled request template.\n"),
    ]

    for title, details in sections:
        text_widget.insert(tk.END, f"{title}\n", "bold")
        text_widget.insert(tk.END, f"{details}\n")

    text_widget.insert(tk.END, "Need help or have feedback?\n", "bold")
    text_widget.insert(tk.END, "- ")
    text_widget.insert(tk.END, "Report a Bug\n", "bug_link")
    text_widget.insert(tk.END, "- ")
    text_widget.insert(tk.END, "Send a Suggestion\n", "suggestion_link")

    bug_link = (
        "mailto:REPLACE_ME"
        "?subject=ETA%20Calculator%20Bug%20Report"
        "&body=Hi%20Team%2C%0A%0AI%20found%20a%20bug%20in%20the%20ETA%20Calculator.%20Here%20are%20the%20details%3A%0A%0A"
        "Issue%3A%0A"
        "%0A"
        "Steps%20to%20Reproduce%3A%0A"
        "%0A"
        "Expected%20Behavior%3A%0A"
        "%0A"
        "Actual%20Behavior%3A%0A"
        "%0A"
        "Thanks%21"
    )

    suggestion_link = (
        "mailto:REPLACE_ME"
        "?subject=ETA%20Calculator%20Suggestion"
        "&body=Hi%20Team%2C%0A%0AI%20have%20a%20suggestion%20for%20improving%20the%20ETA%20Calculator%3A%0A%0A"
        "- Feature Idea%3A%0A"
        "- Why%20It%20Would%20Be%20Helpful%3A%0A%0A"
        "Thanks%21"
    )

    text_widget.tag_configure("bug_link", foreground="blue", underline=True)
    text_widget.tag_configure("suggestion_link", foreground="blue", underline=True)
    text_widget.tag_bind("bug_link", "<Button-1>", lambda e: (log_info("🐞 Bug report link clicked"), webbrowser.open(bug_link)))
    text_widget.tag_bind("suggestion_link", "<Button-1>", lambda e: (log_info("💡 Suggestion link clicked"), webbrowser.open(suggestion_link)))

    text_widget.config(state=tk.DISABLED)






DOCUMENTS = Path.home() / "Documents" / "Transit Time Calculator"
DOCUMENTS.mkdir(parents=True, exist_ok=True)
ZIP_CACHE_PATH = DOCUMENTS / "zip_county_cache.json"



if ZIP_CACHE_PATH.exists():
    with open(ZIP_CACHE_PATH, "r") as f:
        zip_cache = json.load(f)
else:
    zip_cache = {}

def save_zip_cache():
    with open(ZIP_CACHE_PATH, "w") as f:
        json.dump(zip_cache, f, indent=2)





def reverse_geocode_state_and_county(lat, lon, retries=3, delay=1):
    import random
    rounded_key = f"{round(lat, 5)},{round(lon, 5)}"
    cache_path = os.path.join(documents_path, "zip_state_cache.json")
    
    try:
        with open(cache_path, "r") as f:
            cache = json.load(f)
    except:
        cache = {}

    if rounded_key in cache:
        entry = cache[rounded_key]
        return entry.get("state", ""), entry.get("county", "")

    url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
    headers = {"User-Agent": "Transit-Alert-Script"}

    for attempt in range(1, retries + 1):
        try:
            log_debug(f"Attempt {attempt} - Reverse geocoding {lat}, {lon}")
            response = requests.get(url, headers=headers, timeout=5)
            data = response.json().get("address", {})
            state = data.get("state", "")
            county = data.get("county", "").replace(" County", "")
            if state or county:
                cache[rounded_key] = {"state": state, "county": county}
                with open(cache_path, "w") as f:
                    json.dump(cache, f, indent=2)
                log_info(f"✅ Geocoded {lat},{lon} to {state}, {county}")
                return state, county
        except Exception as e:
            log_warning(f"Unexpected error during reverse geocoding: {e}")
            time.sleep(random.uniform(1.2, 2.5))

    log_error(f"Reverse geocoding failed after {retries} attempts for {lat},{lon}")
    log_debug(f"Fallback label used — reverse geocoding completely failed: Coordinates {lat:.2f}, {lon:.2f}")
    return "", ""





def get_spaced_weather_points(coords, desired_count=4, min_miles_between=75):
    from geopy.distance import geodesic

    if not coords:
        return []

    sampled = [coords[0]]
    last = coords[0]

    for point in coords[1:]:
        distance = geodesic(last, point).miles
        if distance >= min_miles_between:
            sampled.append(point)
            last = point
        if len(sampled) >= desired_count:
            break

    if coords[-1] not in sampled:
        sampled.append(coords[-1])

    return sampled






def save_zip_cache():
    try:
        with open(ZIP_CACHE_PATH, "w") as f:
            json.dump(zip_cache, f, indent=2)
        log_info("✅ ZIP cache saved.")
    except Exception as e:
        log_error(f"Failed to save ZIP cache: {e}")


def reverse_geocode_state_and_county(lat, lon):
    key = f"{round(lat, 4)},{round(lon, 4)}"
    now = datetime.utcnow().isoformat()

    if key in zip_cache:
        entry = zip_cache[key]
        if (datetime.fromisoformat(now) - datetime.fromisoformat(entry["timestamp"])).days < 90:
            log_debug(f"ZIP cache hit for {key}")
            return entry["state_abbr"], entry["county"]
        else:
            log_debug(f"ZIP cache expired for {key}")

    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
        log_info(f"🌐 Fetching reverse geocode: {url}")
        resp = requests.get(url, headers={"User-Agent": "eta_calculator"}, timeout=8)
        data = resp.json()
        address = data.get("address", {})

        state_abbr = address.get("ISO3166-2-lvl4", "US-??").split("-")[-1]
        county = address.get("county", "").lower().replace("county", "").strip()

        if state_abbr and county:
            zip_cache[key] = {
                "state_abbr": state_abbr,
                "county": county,
                "timestamp": now
            }
            save_zip_cache()
            log_info(f"✅ Geocoded {lat},{lon} to {state_abbr}, {county}")
        else:
            log_error(f"⚠️ Incomplete address data for {lat},{lon}: {address}")

        return state_abbr, county
    except Exception as e:
        log_error(f"❌ Reverse geocoding failed for {lat},{lon}: {e}")
        return None, None


def get_icon_from_event(event):
    ALERT_ICONS = {
        "flood": "🌊", "wind": "🌬️", "storm": "⛈️", "tornado": "🌪️", "snow": "❄️",
        "rain": "🌧️", "fire": "🔥", "heat": "🥵", "cold": "🥶", "freeze": "🧊",
        "ice": "🧊", "fog": "🌫️", "hurricane": "🌀", "warning": "⚠️",
        "watch": "🔔", "advisory": "📢"
    }
    lowered = event.lower()
    for keyword, icon in ALERT_ICONS.items():
        if keyword in lowered:
            log_debug(f"🛈 Event matched icon: {keyword} → {icon}")
            return icon
    log_debug(f"🛈 No icon match for event: {event}")
    return "⚠️"


def format_eta(end_time):
    if not end_time:
        log_debug("No end_time provided to format_eta.")
        return None
    try:
        end_dt = parser.isoparse(end_time)
        now = datetime.now(end_dt.tzinfo)
        delta = end_dt - now
        if delta.total_seconds() <= 0:
            log_debug(f"ETA already passed: {end_time}")
            return None
        hours, remainder = divmod(delta.total_seconds(), 3600)
        minutes = remainder // 60
        eta_str = f"{int(hours)} hr {int(minutes)} min"
        log_debug(f"Formatted ETA: {eta_str}")
        return eta_str
    except Exception as e:
        log_error(f"Failed to format ETA from {end_time}: {e}")
        return None


import re

# Queries the NOAA weather.gov API for active alerts at a given coordinate.
# Returns a formatted summary string of relevant hazards (e.g., snow, wind, flood).

def get_weather_alerts(lat, lon):
    import os
    import json
    import xml.etree.ElementTree as ET
    import re
    import time
    import requests
    from datetime import datetime, timedelta, timezone
    from collections import defaultdict

    rounded_key = f"{round(lat, 5)},{round(lon, 5)}"
    cache_path = os.path.join(documents_path, "weather_cache.json")

    try:
        with open(cache_path, "r") as f:
            weather_cache = json.load(f)
    except:
        weather_cache = {}

    cache_entry = weather_cache.get(rounded_key)
    if cache_entry:
        expires_str = cache_entry.get("expires_at", "")
        try:
            expires_dt = datetime.fromisoformat(expires_str.replace("Z", "+00:00"))
            now_utc = datetime.now(timezone.utc)
            if expires_dt > now_utc:
                log_info(f"✅ Weather cache hit for {rounded_key} (valid until {expires_str})")
                return [cache_entry["summary"]]
            else:
                log_info(f"🔁 Weather cache expired for {rounded_key} (expired at {expires_str}) — fetching fresh data.")
        except Exception as e:
            log_warning(f"⚠️ Weather cache entry invalid for {rounded_key}: {e}")

    alert_url = f"https://api.weather.gov/alerts/active.atom?point={lat},{lon}"
    headers = {"User-Agent": "REPLACE_ME"}
    log_debug(f"Fetching Atom alerts from {alert_url}")

    try:
        response = requests.get(alert_url, headers=headers, timeout=5)
        response.raise_for_status()
        root = ET.fromstring(response.content)
        ns = {"atom": "http://www.w3.org/2005/Atom"}

        alerts = []
        for entry in root.findall("atom:entry", ns):
            title = entry.find("atom:title", ns).text or ""
            summary = entry.find("atom:summary", ns).text or ""
            updated = entry.find("atom:updated", ns).text or ""
            author = entry.find("atom:author/atom:name", ns)
            office = author.text if author is not None else "NWS"

            start_match = re.search(r'issued (.*?) until', title)
            start_time = start_match.group(1) if start_match else updated
            end_match = re.search(r'until (.*?) by', title)
            end_time = end_match.group(1) if end_match else ""

            title_lower = title.lower()
            icon = "⚠️"
            alert_type = "General"
            for keyword, emoji, label in [
                ("flood", "🌊", "Flood"), ("wind", "🌬️", "Wind"), ("storm", "⛈️", "Storm"),
                ("tornado", "🌪️", "Tornado"), ("snow", "❄️", "Snow"), ("rain", "🌧️", "Rain"),
                ("fire", "🔥", "Fire"), ("heat", "🥵", "Heat"), ("cold", "🥶", "Cold"),
                ("freeze", "🧊", "Ice"), ("ice", "🧊", "Ice"), ("fog", "🌫️", "Fog"),
                ("hurricane", "🌀", "Hurricane"), ("watch", "🔔", "Watch"), ("advisory", "📢", "Advisory")
            ]:
                if keyword in title_lower:
                    icon = emoji
                    alert_type = label
                    break

            alerts.append({
                "title": title,
                "summary": summary,
                "updated": updated,
                "start": start_time,
                "end": end_time,
                "office": office,
                "icon": icon,
                "type": alert_type
            })

        state, county = reverse_geocode_state_and_county(lat, lon)
        full_location = f"{county.title()} County, {state}" if state and county else f"Coordinates {round(lat, 2)}, {round(lon, 2)}"

        if not alerts:
            log_info(f"No active weather alerts for {full_location}")
            return [f"✅ No active weather alerts for {full_location}."]

        grouped_alerts = defaultdict(list)
        summary_types = set()
        alert_emoji = {
            "Flood": "🌊", "Wind": "🌬️", "Storm": "⛈️", "Tornado": "🌪️",
            "Snow": "❄️", "Rain": "🌧️", "Fire": "🔥", "Heat": "🥵",
            "Cold": "🥶", "Ice": "🧊", "Fog": "🌫️", "Hurricane": "🌀",
            "Watch": "🔔", "Advisory": "📢", "General": "⚠️"
        }

        for alert in alerts:
            key = (alert["type"], alert["office"], full_location)
            grouped_alerts[key].append(alert)
            summary_types.add(alert["type"])

        final_alerts = []
        for (atype, office, loc), items in grouped_alerts.items():
            if len(items) == 1:
                a = items[0]
                line = f"{a['icon']} {a['title']} by {office} issued by NWS for {loc}. Please be advised to possible delays."
                final_alerts.append(line)
            else:
                titles = set(i["title"].split(" issued ")[0] for i in items)
                latest_end = max(i.get("end", "") for i in items)
                icon = alert_emoji.get(atype, "⚠️")
                combined_label = " and ".join(sorted(titles))
                start_time = items[0]['start']
                line = (
                    f"{icon} Multiple {combined_label} alerts issued {start_time} until {latest_end} "
                    f"by {office} issued by NWS for {loc}. Please be advised to possible delays."
                )
                final_alerts.append(line)

        summary_line = f"🔎 Alert Summary: {len(final_alerts)} total | " + ", ".join(
            f"{alert_emoji.get(t, '⚠️')} {t}" for t in sorted(summary_types)
        )
        source_line = "📡 Issued by: NWS"
        full_summary = "\n".join(final_alerts + [summary_line, source_line])

        expires_at = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"
        for a in alerts:
            if a.get("end"):
                try:
                    match = re.search(r"(\w+ \d{1,2} at \d{1,2}:\d{2} [AP]M)", a["end"])
                    if match:
                        parsed = datetime.strptime(match.group(1), "%B %d at %I:%M %p")
                        parsed = parsed.replace(year=datetime.now().year)
                        expires_at = parsed.replace(tzinfo=timezone.utc).isoformat()
                        break
                except:
                    continue

        weather_cache[rounded_key] = {
            "summary": full_summary,
            "expires_at": expires_at,
            "fetched_at": datetime.utcnow().isoformat() + "Z"
        }

        with open(cache_path, "w") as f:
            json.dump(weather_cache, f, indent=2)

        log_info(f"Generated {len(final_alerts)} weather alert summaries for {full_location}")
        return final_alerts + [summary_line, source_line]

    except Exception as e:
        log_error(f"Exception in get_weather_alerts(): {e}")
        return [f"⚠️ Error in get_weather_alerts(): {e}"]







def get_city_from_coordinates(lat, lon):
    try:
        url = f"https://nominatim.openstreetmap.org/reverse?lat={lat}&lon={lon}&format=json&addressdetails=1"
        log_debug(f"Geocoding city from {lat},{lon}")
        resp = requests.get(url, headers={"User-Agent": "Transit Time Tool"})
        data = resp.json()
        address = data.get("address", {})
        city = address.get("city") or address.get("town") or address.get("village") or ""
        city = city.lower().strip()
        log_info(f"Resolved city for {lat},{lon}: {city}")
        return city
    except Exception as e:
        log_error(f"Failed to resolve city for {lat},{lon}: {e}")
        return ""


# Uses concurrent requests to fetch weather alerts along multiple route points.
# Combines all alerts into a single summary string.

def get_weather_along_route_parallel(route_coords, max_samples=10):
    if not route_coords or len(route_coords) < 2:
        return "⚠️ Not enough route coordinates to sample weather."

    sampled_points = [route_coords[0]]
    for point in route_coords[1:]:
        last_point = sampled_points[-1]
        if geodesic(last_point, point).miles >= MIN_SAMPLE_DISTANCE_MILES:
            sampled_points.append(point)
            if len(sampled_points) >= max_samples:
                break

    if sampled_points[-1] != route_coords[-1]:
        sampled_points.append(route_coords[-1])

   
    deduped_points = []
    seen = set()
    for lat, lon in sampled_points:
        key = (round(lat, 6), round(lon, 6))
        if key not in seen:
            deduped_points.append((lat, lon))
            seen.add(key)

    log_debug(f"Weather sample count requested: {max_samples} (final unique points: {len(deduped_points)})")
    log_debug(f"Sampled weather points: {[f'{lat:.5f}, {lon:.5f}' for lat, lon in deduped_points]}")

    with ThreadPoolExecutor() as executor:
        results = list(executor.map(lambda p: get_weather_alerts(p[0], p[1]), deduped_points))

    seen_alerts = set()
    flattened = []
    for sublist in results:
        for line in sublist:
            if isinstance(line, str) and line.strip() and line not in seen_alerts:
                flattened.append(line)
                seen_alerts.add(line)

    return "\n".join(flattened) if flattened else "✅ No active weather alerts along the route."











def get_coordinates(address):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": GOOGLE_MAPS_API_KEY
    }

    try:
        log_debug(f"Requesting coordinates for: {address}")
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            log_info(f"Coordinates for '{address}': {location['lat']}, {location['lng']}")
            return (location["lat"], location["lng"])
        else:
            log_error(f"Google Maps API returned status '{data['status']}' for address: {address}")
    except Exception as e:
        log_error(f"Error fetching coordinates for {address}: {e}")
    return None


def haversine_distance(lat1, lon1, lat2, lon2):
    R = 3958.8
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = math.sin(d_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    log_info(f"Haversine distance: {distance:.2f} miles between ({lat1},{lon1}) and ({lat2},{lon2})")
    return distance

# Calculates transit time using mileage, speed, and HOS rules.
# Optionally plans by arrival or departure depending on user toggle.

def calculate_eta():
    try:
        total_miles = float(entry_miles.get())
        average_speed = float(entry_speed.get())
        max_drive_hours = float(entry_drive_hours.get())
        break_hours = float(entry_break_hours.get())
        datetime_str = entry_datetime.get()
        original_time = datetime.strptime(datetime_str, '%m/%d/%Y %I:%M %p')
        now = datetime.now()
        log_info(f"Calculating ETA - miles: {total_miles}, speed: {average_speed}, max hours: {max_drive_hours}, breaks: {break_hours}, datetime: {datetime_str}")

        if planning_by_arrival.get():
            if original_time < now:
                adjusted_time = now
                warning_note = '⚠️ Arrival time entered is in the past — ETA is based on arriving ASAP.\n\n'
                log_info("Arrival mode: time in past, using current time as adjusted_time")
            else:
                adjusted_time = original_time
                warning_note = ''
        else:
            minutes_diff = (now - original_time).total_seconds() / 60
            if minutes_diff > 5:
                adjusted_time = now
                warning_note = '⚠️ Departure time was in the past — adjusted to current time.\n\n'
                log_info("Departure mode: time too far in past, adjusting to now")
            else:
                if minutes_diff > 0:
                    adjusted_time = now
                    warning_note = ''
                    log_info("Departure mode: slightly in past, adjusting to now")
                else:
                    adjusted_time = original_time
                    warning_note = ''
        drive_time_hours = total_miles / average_speed
        full_drive_chunks = int(drive_time_hours // max_drive_hours)
        remaining_drive = drive_time_hours % max_drive_hours
        total_time = full_drive_chunks * (max_drive_hours + break_hours) + remaining_drive
        total_time_rounded = round(total_time, 2)
        num_shifts = full_drive_chunks + (1 if remaining_drive > 0 else 0)
        num_breaks = full_drive_chunks

        if planning_by_arrival.get():
            estimated_departure = adjusted_time - timedelta(hours=total_time)
            output = f"📋 Planning by Arrival (No Traffic)\n{warning_note}Required Arrival: {original_time.strftime('%A, %B %d at %I:%M %p')}\nEstimated Departure: {estimated_departure.strftime('%A, %B %d at %I:%M %p')}\n\n"
        else:
            estimated_arrival = adjusted_time + timedelta(hours=total_time)
            output = f"📋 Planning by Departure (No Traffic)\n{warning_note}Departure Time: {adjusted_time.strftime('%A, %B %d at %I:%M %p')}\nEstimated Arrival: {estimated_arrival.strftime('%A, %B %d at %I:%M %p')}\n\n"

        output += f'Adjusted Drive Time: {round(drive_time_hours, 2)} hrs (based on {total_miles} mi at {average_speed} mph)\nDriving Shifts: {num_shifts}, Breaks Taken: {num_breaks}\nTotal Time Including Breaks: {total_time_rounded} hrs'

        output_box.config(state='normal')
        output_box.delete(1.0, tk.END)
        output_box.insert(tk.END, output)
        output_box.config(state='disabled')
        log_info("ETA calculation complete and displayed to user.")
    except Exception as e:
        log_error(f"Error calculating ETA: {e}")
        messagebox.showerror('Error', f'Error calculating ETA:\n{e}')
        return None

def get_easter_and_good_friday(year):
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    easter_month = (h + l - 7 * m + 114) // 31
    easter_day = ((h + l - 7 * m + 114) % 31) + 1
    easter = date(year, easter_month, easter_day)
    good_friday = easter - timedelta(days=2)
    return easter, good_friday

def get_us_holidays(year):
    def nth_weekday(month, weekday, n):
        d = date(year, month, 1)
        while d.weekday() != weekday:
            d += timedelta(days=1)
        return d + timedelta(weeks=n - 1)

    def last_weekday(month, weekday):
        d = date(year, month + 1, 1) - timedelta(days=1)
        while d.weekday() != weekday:
            d -= timedelta(days=1)
        return d

    holidays = {
        "New Year's Day": date(year, 1, 1),
        "Martin Luther King Jr. Day": nth_weekday(1, 0, 3),
        "Presidents Day": nth_weekday(2, 0, 3),
        "Memorial Day": last_weekday(5, 0),
        "Juneteenth": date(year, 6, 19),
        "Independence Day": date(year, 7, 4),
        "Labor Day": nth_weekday(9, 0, 1),
        "Columbus Day": nth_weekday(10, 0, 2),
        "Veterans Day": date(year, 11, 11),
        "Thanksgiving": nth_weekday(11, 3, 4),
        "Christmas Day": date(year, 12, 25),
    }

    easter, good_friday = get_easter_and_good_friday(year)
    holidays["Good Friday"] = good_friday
    holidays["Easter Sunday"] = easter
    return holidays

# Analyzes route features to suggest driver or equipment notes.
# Flags mountain routes, cold weather, holiday conflicts, or tight arrival windows.

def generate_smart_recommendations(
    total_miles,
    origin_state,
    destination_state,
    route_states,
    pickup_datetime,
    delivery_datetime,
    planning_by_arrival,
    advanced_mode_enabled,
):
    recommendations = []
    log_info(f"Generating smart recommendations for {total_miles} miles, route states: {route_states}")

    if total_miles > 1000:
        recommendations.append("⚠️ Recommend Team Drivers — this route may exceed standard HOS limits if delivery is urgent.")
        log_info("Team drivers recommended for long haul.")

    cold_states = {"ND", "SD", "MN", "WI", "MI", "NY", "VT", "ME", "MT", "ID", "WY"}
    winter_months = {11, 12, 1, 2, 3}
    if (destination_state in cold_states or origin_state in cold_states) and delivery_datetime.month in winter_months:
        recommendations.append("❄️ Consider Reefer or Heated Trailer — destination may require freeze protection.")
        log_info("Cold weather alert added.")

    if planning_by_arrival and pickup_datetime and delivery_datetime:
        drive_time_required = (delivery_datetime - pickup_datetime).total_seconds() / 3600
        if drive_time_required < 12:
            recommendations.append("🚛 Consider Team Drivers — tight window may be difficult for solo drivers.")
            log_info("Tight window: team driver suggestion added.")

    mountain_states = {"CO", "UT", "WY", "MT", "ID"}
    if any(state in mountain_states for state in route_states) and pickup_datetime.month in winter_months:
        recommendations.append("🌨️ Route crosses mountainous regions — allow buffer for delays or weather-related closures.")
        log_info("Mountainous route warning added.")

    if total_miles < 250 and pickup_datetime.weekday() == 5:
        recommendations.append("📦 Consider using Sprinter/Box Truck for faster turnaround on weekend deliveries.")
        log_info("Weekend box truck tip added.")

    year = (pickup_datetime or delivery_datetime or datetime.today()).year
    holidays = get_us_holidays(year)
    for name, h_date in holidays.items():
        if pickup_datetime.date() == h_date or delivery_datetime.date() == h_date:
            recommendations.append(f"🎉 Holiday Alert: {name} — confirm facility hours or closures near pickup/delivery.")
            log_info(f"Holiday alert recommendation added for {name}")

    if not recommendations:
        log_info("No special recommendations generated.")

    return recommendations


# Enhanced ETA calculation that integrates traffic, weather, and smart routing adjustments.
# Uses Google Maps and NOAA APIs to adjust timing and provide planning notes.

def calculate_smart_eta():
    try:
        origin = entry_origin.get()
        destination = entry_destination.get()
        truck_speed = float(entry_speed.get())
        max_drive_hours = float(entry_drive_hours.get())
        break_hours = float(entry_break_hours.get())
        datetime_str = entry_datetime.get()

        if not origin or not destination:
            messagebox.showwarning('Missing Info', 'Please enter both origin and destination.')
            log_error("Missing origin or destination input.")
            return

        log_info(f"Smart ETA start - Origin: {origin}, Destination: {destination}, Speed: {truck_speed}, Max Hours: {max_drive_hours}, Breaks: {break_hours}")

        original_time = datetime.strptime(datetime_str, '%m/%d/%Y %I:%M %p')
        now = datetime.now()

        if planning_by_arrival.get():
            adjusted_time = now if original_time < now else original_time
            warning_note = '⚠️ Arrival time entered is in the past — ETA is based on arriving ASAP.\n\n' if original_time < now else ''
        else:
            minutes_diff = (now - original_time).total_seconds() / 60
            adjusted_time = now if minutes_diff > 5 else (now if minutes_diff > 0 else original_time)
            warning_note = '⚠️ Departure time was in the past — adjusted to current time.\n\n' if minutes_diff > 5 else ''

        log_info(f"Planning mode: {'Arrival' if planning_by_arrival.get() else 'Departure'} — Adjusted Time: {adjusted_time}")

        stops = [entry.get() for entry in waypoint_entries if entry.get().strip()]
        route = [origin] + stops + [destination]
        delivery_times = [entry.get().strip() for entry in delivery_time_entries]

        loop_range = reversed(range(len(route) - 1)) if planning_by_arrival.get() else range(len(route) - 1)
        current_time = original_time if planning_by_arrival.get() else adjusted_time

        total_drive_time = 0
        total_distance = 0
        output_lines = []
        warning_notes = []
        visited_states = set()
        route_coords = []
        route_counties = []

        for i in loop_range:
            origin_leg = route[i]
            dest_leg = route[i + 1]
            log_info(f"Processing leg: {origin_leg} → {dest_leg}")

            departure_ts = int(current_time.timestamp())
            now_ts = int(time.time())
            if departure_ts < now_ts:
                departure_ts = now_ts
                traffic_warning = '⚠️ Traffic data not available for past time — used current traffic instead.\n'
            else:
                traffic_warning = ''

            url = 'https://maps.googleapis.com/maps/api/directions/json'
            params = {
                'origin': origin_leg,
                'destination': dest_leg,
                'departure_time': departure_ts,
                'key': GOOGLE_MAPS_API_KEY
            }
            response = requests.get(url, params=params)
            data = response.json()

            if data['status'] != 'OK':
                raise Exception(data.get('error_message', f'Failed route leg: {origin_leg} → {dest_leg}'))

            leg = data['routes'][0]['legs'][0]
            distance_meters = leg['distance']['value']
            duration_seconds = leg['duration']['value']
            duration_traffic_seconds = leg.get('duration_in_traffic', {}).get('value', duration_seconds)

            delay_seconds = duration_traffic_seconds - duration_seconds
            delay_minutes = round(abs(delay_seconds) / 60)
            traffic_note = f'🚦 Traffic Delay Detected: +{delay_minutes} min' if delay_seconds > 0 else \
                           f'🚀 Traffic faster than usual: -{delay_minutes} min' if delay_seconds < 0 else \
                           '⚠️ No traffic delay detected.'
            traffic_note = traffic_warning + traffic_note

            distance_miles = distance_meters / 1609.34
            car_speed = distance_miles / (duration_traffic_seconds / 3600)
            adjusted_leg_time = distance_miles / truck_speed
            full_shifts = int(adjusted_leg_time // max_drive_hours)
            remaining = adjusted_leg_time % max_drive_hours
            leg_time_with_breaks = full_shifts * (max_drive_hours + break_hours) + remaining

            if i != (len(route) - 2):
                leg_time_with_breaks += DEFAULT_UNLOAD_TIME_HOURS

            total_drive_time += leg_time_with_breaks
            total_distance += distance_miles

            try:
                overview_polyline = data['routes'][0]['overview_polyline']['points']
                decoded_points = decode_polyline(overview_polyline)
                sample_count = get_weather_sample_points()
                sample_points = get_spaced_weather_points(decoded_points, sample_count)

                log_debug(f"Weather sample count requested: {sample_count} (final unique points: {len(sample_points)})")
                log_debug(f"Sampled weather points: {[f'{lat:.5f}, {lon:.5f}' for lat, lon in sample_points]}")

                route_coords.extend(sample_points)

                for lat, lon in sample_points:
                    state, county = reverse_geocode_state_and_county(lat, lon)
                    if county:
                        route_counties.append(county)
                        log_info(f"Added county to route: {county}")
                    if state:
                        visited_states.add(state)
                        log_info(f"Added state to route: {state}")
            except Exception as e:
                log_error(f"Failed to decode polyline or sample coords: {e}")

            states_leg = get_states_from_leg(leg)
            visited_states.update(states_leg)

            if planning_by_arrival.get():
                arrival_time = current_time
                base_eta = arrival_time
                arrival_time -= timedelta(seconds=delay_seconds)
                current_time = arrival_time - timedelta(hours=leg_time_with_breaks)
                stop_label = f'📍 Stop {i + 1}: {origin_leg}'
                time_label = f"    Planned Departure: {current_time.strftime('%A, %B %d at %I:%M %p')}"
            else:
                base_eta = current_time + timedelta(hours=leg_time_with_breaks)
                arrival_time = base_eta + timedelta(seconds=delay_seconds)
                current_time = arrival_time
                stop_label = f'📍 Stop {i + 1}: {dest_leg}'
                time_label = f"    ETA (base): {base_eta.strftime('%A, %B %d at %I:%M %p')}\n    Adjusted ETA with Traffic: {arrival_time.strftime('%A, %B %d at %I:%M %p')}"

            delivery_str = delivery_times[i] if i < len(delivery_times) else ''
            if delivery_str:
                try:
                    target_dt = datetime.strptime(delivery_str, '%m/%d/%Y %I:%M %p')
                    if arrival_time < target_dt:
                        wait_time = (target_dt - arrival_time).total_seconds() / 3600
                        arrival_time = target_dt
                        total_drive_time += wait_time
                        output_lines.append(f'🕒 Wait at Stop {i + 1}: {round(wait_time, 2)} hrs (arrived early)')
                    elif arrival_time > target_dt + timedelta(minutes=15):
                        delay = arrival_time - target_dt
                        late_secs = int(delay.total_seconds())
                        late_hrs = late_secs // 3600
                        late_mins = late_secs % 3600 // 60
                        warning_notes.append(f'🚨 Stop {i + 1} arrival late by {late_hrs} hr {late_mins} min')
                except:
                    output_lines.append(f'⚠️ Invalid delivery time at Stop {i + 1}, skipping window logic.')

            output_lines.append(stop_label)
            if i != 0:
                output_lines.append(f'    Includes {DEFAULT_UNLOAD_TIME_HOURS} hrs from previous stop (loading/unloading)')
            output_lines.append(f'    Distance: {round(distance_miles, 2)} miles')
            output_lines.append(f'    Driving Shifts: {full_shifts + (1 if remaining else 0)}, Breaks Taken: {full_shifts}')
            output_lines.append(time_label)
            output_lines.append(f'    {traffic_note}')
            output_lines.append(f'📊 Adjusted Drive Time: {adjusted_leg_time:.1f} hrs (based on {distance_miles:.1f} mi at {truck_speed:.1f} mph)')
            output_lines.append(f'🕒 Total Time Including Breaks: {leg_time_with_breaks:.1f} hrs\n')

        mode = 'Arrival' if planning_by_arrival.get() else 'Departure'
        label_type = 'Multi-Stop' if advanced_mode.get() and len(route) > 2 else 'Standard'
        output = f'{warning_note}📡 {mode} Planning ({label_type})\n\n' + '\n'.join(output_lines)

        weather_summary = get_weather_along_route_parallel(route_coords, max_samples=get_weather_sample_points())
        output += f"\n{weather_summary}"

        if warning_notes:
            output += '\n\n⚠️ Warnings:\n' + '\n'.join(warning_notes)

        if smart_recommendations_enabled:
            origin_state = get_state_abbr_from_location(origin)
            dest_state = get_state_abbr_from_location(destination)
            pickup_dt = adjusted_time if not planning_by_arrival.get() else adjusted_time - timedelta(hours=total_drive_time)
            delivery_dt = adjusted_time if planning_by_arrival.get() else adjusted_time + timedelta(hours=total_drive_time)

            log_info(f"Matched route states: {list(visited_states)}")
            recommendations = generate_smart_recommendations(
                total_miles=total_distance,
                origin_state=origin_state,
                destination_state=dest_state,
                route_states=list(visited_states),
                pickup_datetime=pickup_dt,
                delivery_datetime=delivery_dt,
                planning_by_arrival=planning_by_arrival.get(),
                advanced_mode_enabled=advanced_mode.get(),
            )

            if recommendations:
                output += '\n\n💡 Smart Recommendations:\n' + '\n'.join(recommendations)
        else:
            output += "\n\n💡 Smart Recommendations are currently disabled. Enable them in ⚙️ Settings."

        output_box.config(state='normal')
        output_box.delete(1.0, tk.END)
        output_box.insert(tk.END, output)
        output_box.config(state='disabled')

        log_info("Smart ETA calculation complete.")

    except Exception as e:
        log_error(f"Smart ETA calculation failed: {e}")
        messagebox.showerror('Error', f'Something went wrong:\n{e}')













# === BUTTONS AND OUTPUT WIDGETS ===

tk.Button(root, text='Calculate ETA (No Traffic)', bg='#004080', fg='white', width=25, command=calculate_eta).grid(row=12, column=0, pady=(10, 5))
tk.Button(root, text='Smart Truck ETA (Traffic + Breaks)', bg='#800000', fg='white', width=30, command=calculate_smart_eta).grid(row=12, column=1, pady=(10, 5))
tk.Button(root, text='📋 Copy to Clipboard', bg='gray20', fg='white', width=25, command=copy_to_clipboard).grid(row=12, column=2, pady=(10, 5), padx=(5, 10))


# ETA Output Frame
output_frame = tk.Frame(root)
output_frame.grid(row=10, column=0, columnspan=5, padx=10, pady=(5, 10), sticky='nsew')

# Make the row and column expandable
root.grid_rowconfigure(10, weight=1)
root.grid_columnconfigure(0, weight=1)



# Scrollable text widget
output_box = ScrolledText(output_frame, wrap='word', height=10, font=('Segoe UI', 10))
output_box.pack(fill='both', expand=True)
output_box.config(state='disabled')


waypoint_entries = []
delivery_time_entries = []
waypoint_widgets = []


def add_waypoint():
    row = 14 + len(waypoint_entries)
    label = tk.Label(root, text=f'Stop {len(waypoint_entries) + 1} Address:')
    label.grid(row=row, column=0, sticky='e', padx=5, pady=2)
    waypoint_entry = tk.Entry(root, width=30)
    waypoint_entry.grid(row=row, column=1, padx=5, pady=2)
    delivery_label = tk.Label(root, text='Delivery Time (optional):')
    delivery_label.grid(row=row, column=2, sticky='e', padx=5)
    delivery_entry = tk.Entry(root, width=20)
    delivery_entry.grid(row=row, column=3, padx=5)
    remove_button = tk.Button(root, text='❌', command=lambda: remove_waypoint(row, label, waypoint_entry, delivery_label, delivery_entry, remove_button))
    remove_button.grid(row=row, column=4, padx=5)
    waypoint_entries.append(waypoint_entry)
    delivery_time_entries.append(delivery_entry)
    waypoint_widgets.append((label, waypoint_entry, delivery_label, delivery_entry, remove_button))
    log_info(f"Added waypoint {len(waypoint_entries)} row: {row}")

def remove_waypoint(row, label, wp_entry, del_label, del_entry, btn):
    label.destroy()
    wp_entry.destroy()
    del_label.destroy()
    del_entry.destroy()
    btn.destroy()
    try:
        index = waypoint_entries.index(wp_entry)
        waypoint_entries.pop(index)
        delivery_time_entries.pop(index)
        waypoint_widgets.pop(index)
        refresh_waypoint_labels()
        log_info(f"Removed waypoint at row {row}")
    except Exception as e:
        log_error(f"Failed to remove waypoint: {e}")

def clear_waypoints():
    try:
        for widgets in waypoint_widgets:
            for widget in widgets:
                widget.destroy()
        waypoint_entries.clear()
        delivery_time_entries.clear()
        waypoint_widgets.clear()
        log_info("Cleared all waypoints.")
    except Exception as e:
        log_error(f"Error clearing waypoints: {e}")

def refresh_waypoint_labels():
    try:
        for i, (label, *_rest) in enumerate(waypoint_widgets):
            label.config(text=f'Stop {i + 1} Address:')
        log_info("Refreshed waypoint labels.")
    except Exception as e:
        log_error(f"Failed to refresh waypoint labels: {e}")


def open_detention_calculator():
    from datetime import datetime, timedelta
    import tkinter as tk
    from tkinter import messagebox

    def calculate_detention():
        try:
            fmt = "%I:%M %p"
            arrival = datetime.strptime(entry_arrival.get(), fmt)
            loaded = datetime.strptime(entry_loaded.get(), fmt)

            if loaded <= arrival:
                loaded += timedelta(days=1)

            time_diff = loaded - arrival
            detention_hours = max(0, (time_diff.total_seconds() / 3600) - 2)

            quarter_hours = round(detention_hours * 4) / 4
            detention_pay = round(quarter_hours * DEFAULT_DETENTION_RATE, 2)

            result_label.config(
                text=f"Detention: ${detention_pay:.2f} ({quarter_hours:.2f} hrs)"
            )
            log_info(f"Detention calculated: ${detention_pay:.2f} for {quarter_hours:.2f} hrs (arrival: {arrival}, loaded: {loaded})")

        except Exception as e:
            log_error(f"Failed to calculate detention: {e}")
            messagebox.showerror("Error", f"Invalid time format: {e}")

    win = create_toplevel_window(tk._default_root)
    win.title("Detention Calculator")
    win.geometry("300x200")
    win.transient(root)
    win.grab_set()

    tk.Label(win, text="Arrival Time (e.g. 10:00 AM):").pack()
    entry_arrival = tk.Entry(win)
    entry_arrival.pack()

    tk.Label(win, text="Loaded Time (e.g. 1:00 PM):").pack()
    entry_loaded = tk.Entry(win)
    entry_loaded.pack()

    tk.Button(win, text="Calculate Detention", command=calculate_detention).pack(pady=10)
    result_label = tk.Label(win, text="")
    result_label.pack()

    apply_theme(win)
    log_info("Detention Calculator window opened.")






def open_settings_window():
    theme_options = {
        "Light Mode": {"bg": "white", "fg": "black"},
        "Dark Mode": {"bg": "#202020", "fg": "white"},
        "Slate Gray": {"bg": "darkgray", "fg": "black"},
        "Midnight Blue": {"bg": "#191970", "fg": "white"},
        "Forest Green": {"bg": "#228B22", "fg": "white"},
        "Royal Purple": {"bg": "#6A0DAD", "fg": "white"},
        "Steel Blue": {"bg": "#4682B4", "fg": "white"},
        "Desert Tan": {"bg": "#D2B48C", "fg": "black"},
        "Sky Blue": {"bg": "#87CEEB", "fg": "black"},
        "Crimson": {"bg": "#DC143C", "fg": "white"},
        "Coral Sunset": {"bg": "#FF6F61", "fg": "white"},
        "Cool Teal": {"bg": "#008080", "fg": "white"},
        "Sunburst Orange": {"bg": "#FFA500", "fg": "#2E1A00"},
        "Neon Green": {"bg": "#39FF14", "fg": "#000000"},
        "Hot Pink Punch": {"bg": "#FF69B4", "fg": "#2F004F"},
        "Aqua Splash": {"bg": "#00FFFF", "fg": "#004040"},
        "Mint Cream": {"bg": "#F5FFFA", "fg": "#003366"},
        "Pastel Peach": {"bg": "#FFDAB9", "fg": "#5C4033"},
        "Lavender Mist": {"bg": "#E6E6FA", "fg": "#4B0082"},
        "Soft Lilac": {"bg": "#D8BFD8", "fg": "#333333"},
        "Powder Blue": {"bg": "#B0E0E6", "fg": "#003366"},
        "Wheat Beige": {"bg": "#F5DEB3", "fg": "#3C2F2F"},
        "Charcoal Glow": {"bg": "#36454F", "fg": "#FFD700"},
        "High Contrast": {"bg": "#000000", "fg": "#FFFF00"},
        "Obsidian": {"bg": "#0B0C10", "fg": "#C5C6C7"},
        "Graphite": {"bg": "#2F4F4F", "fg": "#F8F8FF"},
        "Deep Sea Blue": {"bg": "#001F3F", "fg": "#7FDBFF"},
    }

    config = load_config()
    config.setdefault("default_origin", "Flint, MI")
    config.setdefault("default_destination", "Dallas, TX")
    config.setdefault("default_unload_hours", 1.0)
    config.setdefault("default_detention_rate", 50.0)
    config.setdefault("default_mph", 50.0)
    config.setdefault("selected_theme", "Light Mode")
    config.setdefault("smart_recommendations_enabled", True)
    config.setdefault("weather_sample_points", 4)
    config.setdefault("default_weather_sample_spacing", 75.0)
    save_config(config)
    log_info("Initialized config with default values where missing.")

    def apply_settings():
        try:
            global DEFAULT_UNLOAD_TIME_HOURS, DEFAULT_DETENTION_RATE, DEFAULT_AVERAGE_MPH
            global smart_recommendations_enabled, WEATHER_SAMPLE_POINTS
            
            global MIN_SAMPLE_DISTANCE_MILES
            MIN_SAMPLE_DISTANCE_MILES = float(entry_sample_spacing.get())


            smart_recommendations_enabled = smart_recommendations_var.get()
            default_origin = entry_origin_default.get()
            default_destination = entry_destination_default.get()
            unload_hours = float(entry_unload.get())
            detention_rate = float(entry_detention_rate.get())
            average_mph = float(entry_mph.get())
            selected_theme = theme_var.get()
            sample_count = weather_slider.get()
            sample_spacing = float(entry_sample_spacing.get())
            if sample_spacing < 10: sample_spacing = 10
            if sample_spacing > 300: sample_spacing = 300

            DEFAULT_UNLOAD_TIME_HOURS = unload_hours
            DEFAULT_DETENTION_RATE = detention_rate
            DEFAULT_AVERAGE_MPH = average_mph
            WEATHER_SAMPLE_POINTS = sample_count

            entry_origin.delete(0, tk.END)
            entry_origin.insert(0, default_origin)
            entry_destination.delete(0, tk.END)
            entry_destination.insert(0, default_destination)
            entry_speed.delete(0, tk.END)
            entry_speed.insert(0, str(int(average_mph)) if average_mph == int(average_mph) else str(average_mph))

            colors = theme_options[selected_theme]
            root.config(bg=colors["bg"])
            for widget in root.winfo_children():
                try:
                    widget.config(bg=colors["bg"], fg=colors["fg"])
                except:
                    pass

            config_data = {
                "default_origin": default_origin.strip(),
                "default_destination": default_destination.strip(),
                "default_unload_hours": unload_hours,
                "selected_theme": selected_theme,
                "default_detention_rate": detention_rate,
                "default_mph": average_mph,
                "smart_recommendations_enabled": smart_recommendations_var.get(),
                "weather_sample_points": sample_count,
                "default_weather_sample_spacing": float(entry_sample_spacing.get())
            }

            save_config(config_data)
            settings_win.destroy()

            log_info(f"Settings updated: Origin={default_origin}, Destination={default_destination}, "
                     f"Unload={unload_hours}, Detention=${detention_rate}/hr, Speed={average_mph} mph, "
                     f"Theme='{selected_theme}', SmartRecs={smart_recommendations_enabled}, "
                     f"WeatherPoints={sample_count}, MinDistance={sample_spacing}")
        except Exception as e:
            log_error(f"Error applying settings: {e}")
            messagebox.showerror("Settings Error", f"Could not apply settings:\n{e}\n\nTip: Make sure no fields are left empty.")

    settings_win = create_toplevel_window(root)
    settings_win.title("ETA Calculator Settings")
    settings_win.geometry("460x620")
    settings_win.transient(root)
    settings_win.grab_set()

    form = tk.Frame(settings_win)
    form.pack(pady=20)

    tk.Label(form, text="Default Origin:").grid(row=0, column=0, sticky="e", padx=5, pady=2)
    entry_origin_default = tk.Entry(form, width=30)
    entry_origin_default.grid(row=0, column=1, pady=2)
    entry_origin_default.insert(0, config["default_origin"])

    tk.Label(form, text="Default Destination:").grid(row=1, column=0, sticky="e", padx=5, pady=2)
    entry_destination_default = tk.Entry(form, width=30)
    entry_destination_default.grid(row=1, column=1, pady=2)
    entry_destination_default.insert(0, config["default_destination"])

    tk.Label(form, text="Unload Time (hrs):").grid(row=2, column=0, sticky="e", padx=5, pady=2)
    entry_unload = tk.Entry(form, width=10)
    entry_unload.grid(row=2, column=1, sticky="w", pady=2)
    entry_unload.insert(0, str(config["default_unload_hours"]))

    tk.Label(form, text="Detention Rate ($/hr):").grid(row=3, column=0, sticky="e", padx=5, pady=2)
    entry_detention_rate = tk.Entry(form, width=10)
    entry_detention_rate.grid(row=3, column=1, sticky="w", pady=2)
    entry_detention_rate.insert(0, str(config["default_detention_rate"]))

    tk.Label(form, text="Avg Speed (MPH):").grid(row=4, column=0, sticky="e", padx=5, pady=2)
    entry_mph = tk.Entry(form, width=10)
    entry_mph.grid(row=4, column=1, sticky="w", pady=2)
    mph_val = config["default_mph"]
    entry_mph.insert(0, str(int(mph_val)) if mph_val == int(mph_val) else str(mph_val))

    tk.Label(form, text="Theme:").grid(row=5, column=0, sticky="e", padx=5, pady=5)
    theme_var = tk.StringVar(value=config["selected_theme"])
    theme_menu = tk.OptionMenu(form, theme_var, *theme_options.keys())
    theme_menu.grid(row=5, column=1, sticky="w")

    tk.Label(form, text="Min Miles Between Weather Checkpoints:").grid(row=6, column=0, sticky="e", padx=5, pady=2)
    entry_sample_spacing = tk.Entry(form, width=10)
    entry_sample_spacing.grid(row=6, column=1, sticky="w", pady=2)
    entry_sample_spacing.insert(0, str(config.get("default_weather_sample_spacing", 75.0)))

    smart_recommendations_var = tk.BooleanVar()
    smart_recommendations_var.set(config["smart_recommendations_enabled"])
    tk.Checkbutton(
        settings_win,
        text="✅ Enable Smart Recommendations",
        variable=smart_recommendations_var
    ).pack(pady=(10, 0))

    tk.Label(settings_win, text="Weather Checkpoints (Adding checkpoints may increase calculation time):").pack(pady=(20, 0))
    weather_slider = tk.Scale(
        settings_win,
        from_=2,
        to=20,
        orient="horizontal",
        length=200
    )
    weather_slider.set(config["weather_sample_points"])
    weather_slider.pack()

    tk.Button(settings_win, text="💾 Save & Close", command=apply_settings).pack(pady=20)
    tk.Button(settings_win, text="🪟 Open Debug Console", command=open_console_viewer).pack(pady=(5, 0))

    apply_theme(settings_win)
    log_info("Settings window opened.")











def render_layout_on_canvas(canvas_container, canvas, pallet_instances, equipment_dimensions, scale=2):
    log_info("Rendering pallet layout on canvas...")

    canvas.delete("all")

    max_x = max((p["x"] + p["width"]) for p in pallet_instances) if pallet_instances else equipment_dimensions["width"]
    max_y = max((p["y"] + p["depth"]) for p in pallet_instances) if pallet_instances else equipment_dimensions["length"]

    canvas_width = int(max_x * scale)
    canvas_height = int(max_y * scale)

    canvas.config(scrollregion=(0, 0, canvas_width, canvas_height), width=min(canvas_width, 1000), height=500)
    log_info(f"Canvas dimensions set: width={canvas_width}, height={canvas_height}, scale={scale}")

    for idx, pallet in enumerate(pallet_instances):
        x = pallet["x"] * scale
        y = pallet["y"] * scale
        w = pallet["width"] * scale
        h = pallet["depth"] * scale
        color = "#4a90e2" if idx % 2 == 0 else "#7ed6df"

        canvas.create_rectangle(x, y, x + w, y + h, fill=color, outline="black")
        canvas.create_text(
            x + w / 2,
            y + h / 2,
            text=pallet["id"],
            fill="white",
            font=("Arial", 10, "bold")
        )

        log_info(f"Rendered pallet {pallet['id']} at ({pallet['x']}, {pallet['y']}) with size {pallet['width']}x{pallet['depth']}")

    if not hasattr(canvas_container, "scrollbars_attached"):
        from tkinter import Scrollbar, HORIZONTAL, VERTICAL, RIGHT, BOTTOM, X, Y

        h_scroll = Scrollbar(canvas_container, orient=HORIZONTAL, command=canvas.xview)
        v_scroll = Scrollbar(canvas_container, orient=VERTICAL, command=canvas.yview)

        canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

        h_scroll.grid(row=1, column=0, sticky='ew')
        v_scroll.grid(row=0, column=1, sticky='ns')

        canvas_container.scrollbars_attached = True
        log_info("Scrollbars attached to canvas.")

    log_info("Pallet layout rendering complete.")


def load_custom_equipment():
    path = Path.home() / "Documents" / "Transit Time Calculator" / "custom_equipment.json"
    if path.exists():
        try:
            with open(path, "r") as f:
                return json.load(f)
        except Exception as e:
            print("Error loading custom equipment:", e)
    return {}

def open_linear_feet_calculator():
    import tkinter as tk
    from tkinter import messagebox
    import traceback

    equipment_data = get_equipment_data()
    custom_data = load_custom_equipment()
    equipment_data.update(custom_data)

    lf_window = create_toplevel_window(tk._default_root)
    lf_window.title("📏 Linear Feet Calculator")
    lf_window.geometry("1200x800")

    pallet_coords = []
    fit_check_data = {}

    tk.Label(lf_window, text="Equipment Type:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
    equipment_var = tk.StringVar(value="Cargo Van")
    tk.OptionMenu(lf_window, equipment_var, *equipment_data.keys()).grid(row=0, column=1, sticky='w', padx=5, pady=5)

    custom_check = tk.BooleanVar()
    tk.Checkbutton(lf_window, text="Custom Equipment", variable=custom_check).grid(row=0, column=2, columnspan=2, sticky='w')

    interior_fields, door_fields = {}, {}
    for i, (label, key) in enumerate([
        ("Interior Length (in)", "length"),
        ("Interior Width (in)", "width"),
        ("Interior Height (in)", "height")
    ], start=1):
        tk.Label(lf_window, text=label + ":").grid(row=i, column=0, sticky='e')
        interior_fields[key] = tk.Entry(lf_window, width=10)
        interior_fields[key].grid(row=i, column=1, sticky='w')

    tk.Label(lf_window, text="Door Width (in):").grid(row=4, column=0, sticky='e')
    door_fields["width"] = tk.Entry(lf_window, width=10)
    door_fields["width"].grid(row=4, column=1, sticky='w')

    tk.Label(lf_window, text="Door Height (in):").grid(row=5, column=0, sticky='e')
    door_fields["height"] = tk.Entry(lf_window, width=10)
    door_fields["height"].grid(row=5, column=1, sticky='w')

    entry_eq_name = tk.Entry(lf_window, width=20)
    entry_eq_name.grid(row=6, column=1, sticky='w')
    tk.Label(lf_window, text="Name for Custom Save:").grid(row=6, column=0, sticky='e')

    tk.Button(lf_window, text="💾 Save Custom Equipment", command=lambda: save_equipment(entry_eq_name, interior_fields, door_fields)).grid(row=6, column=2, columnspan=2)

    tk.Label(lf_window, text="Pallets:", font=('Arial', 10, 'bold')).grid(row=7, column=0, pady=(10, 0), sticky='w')
    pallet_frame = tk.Frame(lf_window)
    pallet_frame.grid(row=8, column=0, columnspan=8, padx=10, pady=5, sticky='nsew')

    headers = ["Length (in)", "Width (in)", "Height (in)", "Quantity", "Stackable", "Stack Height", "Turnable", ""]
    for col, header in enumerate(headers):
        tk.Label(pallet_frame, text=header, font=('Arial', 9, 'bold')).grid(row=0, column=col, padx=2, pady=2)

    pallet_rows = []
    tk.Button(lf_window, text="+ Add Pallet", command=lambda: add_pallet_row(pallet_frame, pallet_rows)).grid(row=9, column=0, columnspan=2, pady=10)
    add_pallet_row(pallet_frame, pallet_rows)

    tk.Label(lf_window, text="Result Output:", font=('Arial', 10, 'bold')).grid(row=11, column=0, sticky='w', padx=5)
    output_box = tk.Text(lf_window, wrap=tk.WORD, height=10, width=120)
    output_box.grid(row=12, column=0, columnspan=8, padx=10, pady=(0, 10), sticky='nsew')
    output_box.config(state=tk.DISABLED)

    def display_output(text):
        output_box.config(state=tk.NORMAL)
        output_box.delete("1.0", tk.END)
        output_box.insert(tk.END, text)
        output_box.config(state=tk.DISABLED)

    def update_fields(*args):
        selected = equipment_var.get()
        is_custom = custom_check.get()
        if not is_custom and selected in equipment_data:
            dims = equipment_data[selected]
            for key in ["length", "width", "height"]:
                interior_fields[key].config(state="normal")
                interior_fields[key].delete(0, tk.END)
                interior_fields[key].insert(0, str(dims["interior"][key]))
                interior_fields[key].config(state="readonly")
            for key in ["width", "height"]:
                door_fields[key].config(state="normal")
                door_fields[key].delete(0, tk.END)
                door_fields[key].insert(0, str(dims["door"][key]))
                door_fields[key].config(state="readonly")
            entry_eq_name.delete(0, tk.END)
            entry_eq_name.config(state="disabled")
        else:
            for f in interior_fields.values(): f.config(state="normal")
            for f in door_fields.values(): f.config(state="normal")
            entry_eq_name.config(state="normal")

    equipment_var.trace_add("write", update_fields)
    custom_check.trace_add("write", update_fields)
    update_fields()

    def calculate():
        nonlocal pallet_coords, fit_check_data
        try:
            selected_equipment = equipment_var.get()
            fit_check_data = {**equipment_data}

            if custom_check.get():
                try:
                    fit_check_data["__custom__"] = {
                        "interior": {
                            "length": float(interior_fields["length"].get()),
                            "width": float(interior_fields["width"].get()),
                            "height": float(interior_fields["height"].get())
                        },
                        "door": {
                            "width": float(door_fields["width"].get()),
                            "height": float(door_fields["height"].get())
                        }
                    }
                    selected_equipment = "__custom__"
                except:
                    display_output("❌ Invalid custom equipment dimensions.")
                    return

            trailer_dims = fit_check_data[selected_equipment]["interior"]
            trailer_width = trailer_dims["width"]
            trailer_height = trailer_dims["height"]

            total_length_in, debug_log, pallet_coords = calculate_pallet_space(pallet_rows, trailer_width, trailer_height)

            best_fit = check_fit_and_suggest_upgrade_full_recalc(
                pallet_rows, selected_equipment, fit_check_data, message_output_box=output_box
            )

            result_msg = f"✅ Total Linear Feet Required: {total_length_in / 12:.2f} ft"
            display_output(result_msg)

            if best_fit and best_fit != selected_equipment:
                print(f"💡 Best Fit Returned: {best_fit}")
                def switch_equipment():
                    equipment_var.set(best_fit)
                    popup.destroy()
                    calculate()

                popup = tk.Toplevel()
                popup.title("Suggested Equipment Upgrade")
                popup.geometry("400x120+700+400")
                tk.Label(
                    popup,
                    text=f"Would you like to switch to:\n{best_fit} ({fit_check_data[best_fit]['interior']['length']}\" interior)?",
                    padx=20, pady=10
                ).pack()
                tk.Button(popup, text="Yes", command=switch_equipment).pack(pady=5)
                tk.Button(popup, text="No", command=popup.destroy).pack()
            else:
                print("❌ No popup triggered. Either no suggestion or same equipment.")

        except Exception as e:
            traceback.print_exc()
            display_output(f"❌ Calculation error: {e}")

    def open_layout_window():
        try:
            selected_equipment = equipment_var.get()
            trailer_dims = fit_check_data[selected_equipment]["interior"]

            layout_win = tk.Toplevel()
            layout_win.title("Pallet Layout View")
            layout_win.geometry("1400x800")

            warning_label = tk.Label(
                layout_win,
                text="⚠ This is a rough approximation.\nWeight & load balancing not considered.",
                fg="red",
                font=("Arial", 12, "bold"),
                justify="right",
                anchor="ne"
            )
            warning_label.pack(side="top", anchor="ne", padx=10, pady=10)

            canvas_container = tk.Frame(layout_win)
            canvas_container.pack(fill="both", expand=True)

            layout_canvas = tk.Canvas(canvas_container, bg="white")
            layout_canvas.grid(row=0, column=0, sticky="nsew")

            h_scroll = tk.Scrollbar(canvas_container, orient="horizontal", command=layout_canvas.xview)
            v_scroll = tk.Scrollbar(canvas_container, orient="vertical", command=layout_canvas.yview)
            layout_canvas.configure(xscrollcommand=h_scroll.set, yscrollcommand=v_scroll.set)

            h_scroll.grid(row=1, column=0, sticky="ew")
            v_scroll.grid(row=0, column=1, sticky="ns")

            canvas_container.grid_rowconfigure(0, weight=1)
            canvas_container.grid_columnconfigure(0, weight=1)

            layout_win.update_idletasks()

            print("🧩 Preview Debug:", pallet_coords, trailer_dims)

            render_layout_on_canvas(canvas_container, layout_canvas, pallet_coords, trailer_dims)

        except Exception as e:
            traceback.print_exc()
            messagebox.showerror("Error", f"Failed to open layout window:\n{e}")


    tk.Button(lf_window, text="📏 Calculate", command=calculate).grid(row=10, column=0, columnspan=2, pady=10)
    tk.Button(lf_window, text="👁 View Layout", command=open_layout_window).grid(row=10, column=2, columnspan=2, pady=10)
    apply_theme(lf_window)







def save_equipment(entry_eq_name, interior_fields, door_fields):
    try:
        name = entry_eq_name.get().strip()
        length = float(interior_fields["length"].get())
        width = float(interior_fields["width"].get())
        height = float(interior_fields["height"].get())
        door_w = float(door_fields["width"].get())
        door_h = float(door_fields["height"].get())
        if not name:
            messagebox.showerror("Error", "Enter a name for custom equipment.")
            return
        save_custom_equipment(name, length, width, height, door_w, door_h)
    except Exception as e:
        messagebox.showerror("Error", f"Invalid values: {e}")


def get_equipment_data():
    return {
        "Cargo Van": {"interior": {"length": 100, "width": 50, "height": 48}, "door": {"width": 48, "height": 46}},
        "Sprinter Van": {"interior": {"length": 144, "width": 54, "height": 72}, "door": {"width": 49, "height": 70}},
        "Small Straight 12ft": {"interior": {"length": 144, "width": 96, "height": 96}, "door": {"width": 96, "height": 96}},
        "Small Straight 18ft": {"interior": {"length": 216, "width": 96, "height": 96}, "door": {"width": 96, "height": 96}},
        "Large Straight 22ft": {"interior": {"length": 264, "width": 96, "height": 96}, "door": {"width": 96, "height": 96}},
        "Large Straight 24ft": {"interior": {"length": 288, "width": 96, "height": 96}, "door": {"width": 96, "height": 96}},
        "Large Straight 26ft": {"interior": {"length": 312, "width": 96, "height": 96}, "door": {"width": 96, "height": 96}},
        "53' Dry Van": {"interior": {"length": 630, "width": 98, "height": 104}, "door": {"width": 98, "height": 104}},
        "48' Flatbed": {"interior": {"length": 576, "width": 102, "height": 96}, "door": {"width": 102, "height": 96}},
        "53' Flatbed": {"interior": {"length": 636, "width": 102, "height": 96}, "door": {"width": 102, "height": 96}}
    }

from pathlib import Path
import json

def check_fit_and_suggest_upgrade_full_recalc(pallet_rows, selected_equipment, equipment_data, message_output_box=None):
    import math
    from tkinter import BooleanVar

    def log(msg):
        print(msg)
        if message_output_box:
            message_output_box.insert('end', f"{msg}\n")

    if selected_equipment not in equipment_data:
        log(f"❌ Selected equipment '{selected_equipment}' not found.")
        return None

    selected_dims = equipment_data[selected_equipment]["interior"]
    selected_width = selected_dims["width"]
    selected_height = selected_dims["height"]

    def calculate_length_for_equipment(width, height):
        total_length = 0
        pallet_instances = []

        for idx, row in enumerate(pallet_rows, 1):
            try:
                original_length_in = float(row["length"].get())
                original_width_in = float(row["width"].get())
                pallet_height_in = float(row["height"].get())
                quantity = int(row["quantity"].get())
                is_stackable = row["stackable"].get()
                is_turnable = row.get("turnable", BooleanVar(value=True)).get()
                stack_count_requested = int(row["stack_count"].get()) if is_stackable else 1

                rotated = False
                pallet_length_in = original_length_in
                pallet_width_in = original_width_in

                fits_normal = original_width_in <= width
                fits_rotated = original_length_in <= width

                # Reject immediately if the pallet doesn't fit width-wise in any orientation
                if not fits_normal and (not is_turnable or not fits_rotated):
                    log(f"❌ Pallet too wide to fit in trailer width ({width}\"), even with turning.")
                    return float('inf')

                if is_turnable and fits_rotated and (not fits_normal or original_length_in > original_width_in):
                    # Rotate for better fit
                    pallet_length_in, pallet_width_in = original_width_in, original_length_in
                    rotated = True

                # Stack logic
                max_stackable_count = max(height // pallet_height_in, 1)
                actual_stack_count = min(stack_count_requested, max_stackable_count)
                effective_pallets = quantity
                stack_slots_needed = math.ceil(effective_pallets / actual_stack_count)

                for _ in range(stack_slots_needed):
                    pallet_instances.append({
                        "width": pallet_width_in,
                        "depth": pallet_length_in,
                    })

            except Exception as e:
                log(f"❌ Error parsing pallet row {idx}: {e}")
                return float('inf')

        rows = []
        for pallet in pallet_instances:
            placed = False
            for row in rows:
                for segment in row["segments"]:
                    if pallet["depth"] <= segment["depth"] and pallet["width"] <= segment["remaining_width"]:
                        segment["remaining_width"] -= pallet["width"]
                        placed = True
                        break
                if placed:
                    break
            if not placed:
                rows.append({
                    "segments": [{
                        "depth": pallet["depth"],
                        "remaining_width": width - pallet["width"]
                    }]
                })

        total_length = sum(max(seg["depth"] for seg in row["segments"]) for row in rows)
        return total_length

    selected_length = selected_dims["length"]
    required_length = calculate_length_for_equipment(selected_width, selected_height)

    log(f"\n🧠 Real Fit Check with Recalculation")
    log(f"Selected Equipment: {selected_equipment} ({selected_length}\")")
    log(f"Required Length in this trailer: {required_length:.2f}\"")

    if required_length <= selected_length:
        log("✅ Load fits in selected equipment.")
        return selected_equipment

    preferred_order = [
        "Cargo Van", "Sprinter Van",
        "Small Straight 12ft", "Small Straight 18ft",
        "Large Straight 22ft", "Large Straight 24ft", "Large Straight 26ft",
        "53' Dry Van", "48' Flatbed", "53' Flatbed"
    ]

    best_fit = None
    for name in preferred_order:
        if name not in equipment_data:
            continue
        dims = equipment_data[name]["interior"]
        fit_length = calculate_length_for_equipment(dims["width"], dims["height"])
        log(f"🔍 {name}: fits in {fit_length:.2f}\" vs {dims['length']}\" available")
        if fit_length <= dims["length"]:
            best_fit = name
            log(f"🎯 Suggested: {name} ({dims['length']}\" interior)")
            if message_output_box:
                message_output_box.insert('end', f"\n⚠️ Suggested Upgrade: {name} ({dims['length']}\" interior)\n")
            break

    if not best_fit:
        log("❌ No equipment found that can fit this load.")

    return best_fit





def save_custom_equipment(name, length, width, height, door_width, door_height):
    save_path = Path.home() / "Documents" / "Transit Time Calculator"
    save_path.mkdir(parents=True, exist_ok=True)
    save_file = save_path / "custom_equipment.json"

    data = {}
    if save_file.exists():
        try:
            with open(save_file, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    data[name] = {
        "interior": {"length": length, "width": width, "height": height},
        "door": {"width": door_width, "height": door_height}
    }

    with open(save_file, "w") as f:
        json.dump(data, f, indent=2)

    return name


def add_pallet_row(pallet_frame, pallet_rows):
    row = len(pallet_rows) + 1  # offset for header
    row_data = {}

    row_data["length"] = tk.Entry(pallet_frame, width=8)
    row_data["length"].grid(row=row, column=0)

    row_data["width"] = tk.Entry(pallet_frame, width=8)
    row_data["width"].grid(row=row, column=1)

    row_data["height"] = tk.Entry(pallet_frame, width=8)
    row_data["height"].grid(row=row, column=2)

    row_data["quantity"] = tk.Entry(pallet_frame, width=5)
    row_data["quantity"].grid(row=row, column=3)

    row_data["stackable"] = tk.BooleanVar()
    tk.Checkbutton(pallet_frame, variable=row_data["stackable"]).grid(row=row, column=4)

    row_data["stack_count"] = tk.Entry(pallet_frame, width=5)
    row_data["stack_count"].insert(0, "2")
    row_data["stack_count"].grid(row=row, column=5)

    row_data["turnable"] = tk.BooleanVar(value=True)
    tk.Checkbutton(pallet_frame, variable=row_data["turnable"]).grid(row=row, column=6)

    def remove():
        for widget in [
            row_data["length"], row_data["width"], row_data["height"], row_data["quantity"],
            row_data["stack_count"], row_data["remove_btn"], row_data["turnable"]
        ]:
            if hasattr(widget, "grid_forget"):
                widget.grid_forget()
        pallet_rows.remove(row_data)

    row_data["remove_btn"] = tk.Button(pallet_frame, text="Remove", command=remove)
    row_data["remove_btn"].grid(row=row, column=7)

    pallet_rows.append(row_data)


def calculate_pallet_space(pallet_rows, trailer_width_in, trailer_height_in):
    import math
    import tkinter as tk

    log_info("🧮 Starting pallet space calculation...")
    SCALE = 1
    grid_width = int(trailer_width_in * SCALE)
    grid_height = 5000

    grid = [[None for _ in range(grid_width)] for _ in range(grid_height)]

    debug_output = []
    pallet_instances = []

    def can_place(x, y, width, depth):
        for dy in range(y, y + depth):
            if dy >= len(grid):
                return False
            for dx in range(x, x + width):
                if dx >= len(grid[0]) or grid[dy][dx] is not None:
                    return False
        return True

    def place_pallet(pallet_id, width, depth):
        for y in range(0, grid_height - depth):
            for x in range(0, grid_width - width + 1):
                if can_place(x, y, width, depth):
                    for dy in range(y, y + depth):
                        for dx in range(x, x + width):
                            grid[dy][dx] = pallet_id
                    return x, y
        return None, None

    for idx, row in enumerate(pallet_rows, 1):
        try:
            original_length_in = float(row["length"].get())
            original_width_in = float(row["width"].get())
            pallet_height_in = float(row["height"].get())
            quantity = int(row["quantity"].get())
            is_stackable = row["stackable"].get()
            is_turnable = row.get("turnable", tk.BooleanVar(value=True)).get()
            stack_count_requested = int(row["stack_count"].get()) if is_stackable else 1

            max_stackable_count = max(int(trailer_height_in // pallet_height_in), 1)
            actual_stack_count = min(stack_count_requested, max_stackable_count)
            total_slots = math.ceil(quantity / actual_stack_count)

            for slot in range(total_slots):
                id_str = f"R{idx}_P{slot+1}"
                length = int(original_length_in * SCALE)
                width = int(original_width_in * SCALE)
                rotated = False

                x, y = place_pallet(id_str, width, length)

                if x is None and is_turnable:
                    x, y = place_pallet(id_str, length, width)
                    if x is not None:
                        width, length = length, width
                        rotated = True

                if x is not None:
                    pallet_instances.append({
                        "id": id_str,
                        "x": x,
                        "y": y,
                        "width": width,
                        "depth": length,
                        "rotated": rotated,
                        "row": idx
                    })
                    log_info(f"✅ Placed pallet {id_str} at ({x}, {y}) | Rotated: {rotated}")
                else:
                    msg = f"❌ Could not place pallet {id_str}"
                    debug_output.append({"row": idx, "error": msg})
                    log_error(msg)

            debug_output.append({
                "row": idx,
                "original_length_in": original_length_in,
                "original_width_in": original_width_in,
                "used_length_in": length,
                "used_width_in": width,
                "quantity": quantity,
                "pallet_height_in": pallet_height_in,
                "stackable": is_stackable,
                "requested_stack": stack_count_requested,
                "actual_stack": actual_stack_count,
                "stacking_used": is_stackable,
                "turnable": is_turnable,
                "rotated": rotated,
                "trailer_width_in": trailer_width_in,
                "stack_slots_used": total_slots
            })

        except Exception as e:
            error_msg = f"Row {idx} failed during pallet placement: {e}"
            debug_output.append({"row": idx, "error": error_msg})
            log_error(error_msg)

    max_y = max((p["y"] + p["depth"] for p in pallet_instances), default=0)
    total_length_in = max_y

    log_info(f"🧾 Total linear feet required: {total_length_in / 12:.2f} ft")
    log_info("📦 Pallet space calculation complete.")

    return total_length_in, debug_output, pallet_instances



def calculate_ltl_linear_feet_from_entries(pallet_rows, trailer_width_in=98):
    total_rows = 0
    row_width_remaining = trailer_width_in
    current_row_depth = 0
    total_depth_in = 0
    all_pallet_lengths_ft = []

    for pallet in pallet_rows:
        try:
            length_in = float(pallet["entries"][0].get())
            width_in = float(pallet["entries"][1].get())
            quantity = int(pallet["entries"][4].get())
        except:
            continue

        for _ in range(quantity):
            if width_in > row_width_remaining:
                total_rows += 1
                total_depth_in += current_row_depth
                row_width_remaining = trailer_width_in
                current_row_depth = 0

            row_width_remaining -= width_in
            current_row_depth = max(current_row_depth, length_in)
            all_pallet_lengths_ft.append(length_in / 12)

    # Final row depth
    total_depth_in += current_row_depth

    return total_depth_in / 12, all_pallet_lengths_ft  # linear ft, individual pallet lengths







    
    
tk.Button(root, text="⚙️ Settings", command=open_settings_window).grid(row=99, column=0, sticky='w', padx=10, pady=10)
tk.Button(root, text="🖩 Detention Calculator", command=open_detention_calculator).grid(row=99, column=1, sticky='w', padx=10, pady=10)
tk.Button(root, text="📦 Open LTL Density Calculator", command=open_density_calculator).grid(row=99, column=2, sticky='w', padx=10, pady=10)
tk.Button(root, text="❓ Help", command=open_help_window).grid(row=99, column=3, sticky='w', padx=10, pady=10)
tk.Button(root, text="📏 Calculate Linear Feet", bg="#008000", fg="white", width=25, command=open_linear_feet_calculator).grid(row=13, column=0, pady=(10, 5), padx=5)
add_waypoint_button = tk.Button(root, text='➕ Add Waypoint', command=add_waypoint)
add_waypoint_button.grid(row=15, column=0, columnspan=2, sticky='w', padx=5)
add_waypoint_button.grid_remove()

    

apply_config_to_gui(config)


def clean_old_log_entries(log_path, days=7):
    try:
        if not os.path.exists(log_path):
            log_info("Log file does not exist — skipping cleanup.")
            return

        cutoff = datetime.now() - timedelta(days=days)
        kept_lines = []

        with open(log_path, "r", encoding="utf-8-sig") as f:
            for line in f:
                try:
                    if line.startswith("["):
                        ts_str = line[1:20]  # '[2025-04-19 06:06:33]'
                        log_time = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                        if log_time >= cutoff:
                            kept_lines.append(line)
                    else:
                        kept_lines.append(line)  # Keep non-timestamp lines
                except Exception:
                    kept_lines.append(line) 

        with open(log_path, "w", encoding="utf-8-sig") as f:
            f.writelines(kept_lines)

        log_info(f"🧹 Cleaned log — removed entries older than {days} days.")
    except Exception as e:
        log_error(f"❌ Error during log cleanup: {e}")


def on_closing():
    log_info("🚪 Application exit triggered — cleaning up logs.")
    clean_old_log_entries(log_path, days=7)
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)

root.mainloop()
