# WoWAuto - Sequence Runner

A powerful JSON-based automation system for World of Warcraft that only runs when WoW is the active window.

## ✨ Features

- 🎯 **Window Detection**: Only runs when World of Warcraft is active
- 🎲 **Random Variations**: Adds 10% timing randomness for human-like behavior
- 🎰 **Chance System**: Actions can have probability (1-100%)
- ⏱️ **Precise & Random Timing**: Use `duration` for exact timing or let it randomize
- 🖱️ **Mouse Movement**: Human-like mouse movements with settle delays
- ⌨️ **Full Keyboard Support**: W/A/S/D, arrows, F-keys, modifiers, numpad
- 🔁 **Periodic Sequences**: Run actions every N seconds automatically
- 🌐 **Async Support**: Multiple sequences run concurrently

## � Setup & Running

### First Time Setup
1. **Build the environment** (only needed once):
   ```cmd
   env.bat
   ```
   This creates the virtual environment and installs all dependencies.

### Running the Application
2. **Run the test version**:
   ```cmd
   test.bat
   ```
   This activates the virtual environment and launches the GUI interface.

### Manual Python Execution
If you prefer to run Python commands manually:
```cmd
env\Scripts\activate
python formauto.py
```

## �📝 JSON Format

### Basic Key Press
```json
{
  "type": "key",
  "action": "press",
  "key