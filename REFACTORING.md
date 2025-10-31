# WoW Auto - Project Refactoring Complete

## Overview
The project has been reorganized from monolithic files into proper Python packages with modular structure.

## New Structure

### wowauto/ Package
The core automation engine, split into focused modules:

- **`__init__.py`** - Package initialization and exports
- **`__main__.py`** - Entry point when running as module (`python -m wowauto`)
- **`sequence_runner.py`** - Main orchestrator class
- **`sequence_loader.py`** - JSON file loading and parsing
- **`action_executor.py`** - Keyboard and mouse action execution
- **`window_detector.py`** - WoW window detection utilities
- **`key_parser.py`** - Key name parsing (w, a, s, d, arrows, F-keys, numpad, etc.)
- **`README.md`** - Documentation

### formauto/ Package
The GUI application, split into logical components:

- **`__init__.py`** - Package initialization and exports
- **`__main__.py`** - Entry point when running as module (`python -m formauto`)
- **`settings_form.py`** - Main GUI window
- **`settings_manager.py`** - Settings persistence (load/save)
- **`background_runner.py`** - Thread management for non-blocking execution
- **`key_listener.py`** - Global hotkey detection
- **`stop_window.py`** - Always-on-top STOP button widget

### Backward Compatibility
Root-level files maintained as wrappers:

- **`wowauto.py`** - Imports and re-exports from `wowauto` package
- **`formauto.py`** - Imports and re-exports from `formauto` package

## Usage

### Using wowauto
```python
# New modular way (recommended)
from wowauto import SequenceRunner

runner = SequenceRunner(dry_run=False)
runner.load_file("sequences.json")
runner.run_forever()
```

```bash
# Run as module
python -m wowauto
```

```bash
# Old way (still works)
python wowauto.py
```

### Using formauto
```python
# New modular way (recommended)
from formauto import SettingsForm

app = SettingsForm()
app.mainloop()
```

```bash
# Run as module
python -m formauto
```

```bash
# Old way (still works)
python formauto.py
```

## Benefits of Refactoring

### 1. **Modularity**
- Each module has a single, clear responsibility
- Easier to test individual components
- Better code organization

### 2. **Maintainability**
- Smaller files are easier to understand
- Changes to one component don't affect others
- Clear separation of concerns

### 3. **Reusability**
- Import only what you need: `from wowauto import ActionExecutor`
- Components can be used independently
- Easier to build new tools on top

### 4. **Extensibility**
- Easy to add new action types to `ActionExecutor`
- Simple to add new settings to `SettingsManager`
- New key parsers can be added to `key_parser.py`

### 5. **Professional Structure**
- Follows Python package best practices
- `__init__.py` provides clean public API
- `__main__.py` enables module execution

## Module Responsibilities

### wowauto Package

#### SequenceRunner
- Orchestrates all components
- Manages async task lifecycle
- Coordinates window checking with action execution

#### SequenceLoader
- Parses JSON files
- Validates sequence format
- Provides sequence lookup

#### ActionExecutor
- Executes keyboard actions (press, hold, down, up)
- Executes mouse actions (click, move, hold)
- Handles wait and superwait (exact timing)
- Manages chance-based action execution
- Adds human-like randomness (timing, mouse settle delays)

#### WindowDetector
- Checks if WoW is active window
- Configurable window titles
- Adjustable check interval

#### KeyParser
- Maps string names to pynput keys
- Supports: W/A/S/D, arrows, F-keys, modifiers, numpad
- Handles multiple aliases (e.g., "leftarrow", "left_arrow", "arrow_left")

### formauto Package

#### SettingsForm
- Main GUI with tkinter
- Sequence selection (multiple)
- Toggle key configuration
- Start/stop automation control
- Status display

#### SettingsManager
- Saves/loads settings JSON
- Manages settings directory
- Falls back gracefully on errors

#### BackgroundRunner
- Runs SequenceRunner in separate thread
- Non-blocking async loop
- Clean shutdown with timeout

#### GlobalKeyListener
- Uses pynput for global hotkey detection
- Works even when app not focused
- Configurable toggle key

#### StopWindow
- Always-on-top red button
- Positioned in top-right corner
- Quick emergency stop

## File Sizes (Approximate)

### Before
- `wowauto.py`: 559 lines (monolithic)
- `formauto.py`: 536 lines (monolithic)

### After
wowauto package:
- `sequence_runner.py`: ~190 lines
- `action_executor.py`: ~220 lines
- `sequence_loader.py`: ~60 lines
- `window_detector.py`: ~45 lines
- `key_parser.py`: ~150 lines

formauto package:
- `settings_form.py`: ~310 lines
- `background_runner.py`: ~95 lines
- `settings_manager.py`: ~90 lines
- `key_listener.py`: ~60 lines
- `stop_window.py`: ~55 lines

**Total reduction**: From ~1095 lines in 2 files to ~1275 lines in 10+ focused modules
(Slightly more lines due to proper docstrings and structure)

## Testing

Run the packages:
```bash
# Test wowauto
python -m wowauto

# Test formauto GUI
python -m formauto

# Or use backward-compatible entry points
python wowauto.py
python formauto.py
```

## Next Steps

1. **Add Unit Tests**: Create `tests/` directory with pytest
2. **Add Type Hints**: Full type annotations throughout
3. **Add Logging**: Replace print statements with proper logging
4. **Documentation**: Add Sphinx docs in `docs/`
5. **Package Distribution**: Create `setup.py` for pip installation

## Dependencies

No changes to dependencies - still uses:
- pyinstaller==5.13.0
- pillow==9.5.0
- requests==2.31.0
- urllib3==1.26.16
- pywin32==306
- keyboard==0.13.5
- mouse==0.7.1
- pynput==1.7.6

