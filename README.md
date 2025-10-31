# ⚔️ WoW Auto - World of Warcraft Automation System

A powerful JSON-based automation system for World of Warcraft with a beautiful WoW-themed GUI interface.

## ✨ Features

- 🎯 **Window Detection**: Only runs when World of Warcraft is active
- 🎨 **WoW-Themed GUI**: Beautiful brown/gold interface with rounded buttons
- 🖱️ **Human-Like Mouse Movement**: Smooth Bezier curve movements with random offsets (1-2px)
- 🎲 **Random Variations**: 10% timing randomness for realistic behavior
- 🎰 **Chance System**: Actions can have probability (1-100%)
- ⌨️ **Full Keyboard Support**: W/A/S/D, arrows, F-keys, modifiers, numpad
- 🔁 **Periodic Sequences**: Run actions every N seconds automatically
- 🌐 **Async Support**: Multiple sequences run concurrently
- 👁️ **Transparent Overlay**: Draggable stop button that doesn't block gameplay

## 📁 Project Structure

```
wow-auto/
├── wowauto/                    # Core automation package (modular)
│   ├── __init__.py
│   ├── __main__.py
│   ├── sequence_runner.py     # Main orchestrator
│   ├── action_executor.py     # Keyboard/mouse control
│   ├── sequence_loader.py     # JSON parsing
│   ├── window_detector.py     # WoW window detection
│   ├── key_parser.py          # Key mapping
│   └── README.md
│
├── formauto/                   # GUI interface package (modular)
│   ├── __init__.py
│   ├── __main__.py
│   ├── settings_form.py       # Main WoW-themed GUI
│   ├── background_runner.py   # Thread management
│   ├── settings_manager.py    # Settings persistence
│   ├── key_listener.py        # Global hotkeys
│   └── stop_window.py         # Transparent overlay
│
├── wowauto.py                 # Legacy wrapper (backward compatibility)
├── formauto.py                # Legacy wrapper (backward compatibility)
│
├── *.json                     # Sequence files (afkcheck, bloodofthemountain, etc.)
├── requirements.txt           # Python dependencies
├── env.bat                    # Environment setup script
├── test.bat                   # Quick launch script
└── env/                       # Virtual environment (created by env.bat)
```

## 🚀 Setup & Running

### First Time Setup
1. **Build the environment** (only needed once):
   ```cmd
   env.bat
   ```
   This creates the virtual environment and installs all dependencies from `requirements.txt`.

### Running the Application
2. **Launch the GUI**:
   ```cmd
   test.bat
   ```
   This activates the virtual environment and starts the WoW-themed GUI interface.

### Manual Python Execution
If you prefer manual control:
```cmd
env\Scripts\activate
python formauto.py
```

Or run as module:
```cmd
env\Scripts\activate
python -m formauto
```

## 📦 Requirements

- Python 3.9+
- Windows OS (uses ctypes for GUI theming and window detection)
- Dependencies listed in `requirements.txt`:
  - pynput (keyboard/mouse control)
  - keyboard (global hotkeys)
  - mouse (mouse control)
  - Pillow (image processing)

