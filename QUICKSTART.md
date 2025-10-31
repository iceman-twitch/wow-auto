# WoW Auto - Quick Start Guide

## What Changed?

Your project is now organized into proper Python packages! The functionality is the same, but the code is split into focused modules for better maintainability.

## New Folder Structure

```
d:\Github\wow-auto\
├── wowauto/                    # Core automation package
│   ├── __init__.py
│   ├── __main__.py
│   ├── sequence_runner.py      # Main orchestrator
│   ├── action_executor.py      # Keyboard/mouse actions
│   ├── sequence_loader.py      # JSON loading
│   ├── window_detector.py      # WoW window detection
│   ├── key_parser.py           # Key name parsing
│   └── README.md
├── formauto/                   # GUI application package
│   ├── __init__.py
│   ├── __main__.py
│   ├── settings_form.py        # Main window
│   ├── settings_manager.py     # Settings persistence
│   ├── background_runner.py    # Thread management
│   ├── key_listener.py         # Global hotkeys
│   └── stop_window.py          # STOP button widget
├── wowauto.py                  # Backward compatibility wrapper
├── formauto.py                 # Backward compatibility wrapper
├── requirements.txt            # Dependencies (no AI packages)
├── REFACTORING.md              # Detailed refactoring notes
└── README.md                   # Project documentation
```

## How to Run

### Nothing Changed!
Your existing scripts still work:

```bash
# Run automation engine (dry-run mode)
python wowauto.py

# Run GUI
python formauto.py
```

### New Way (Recommended)
```bash
# Run as modules
python -m wowauto
python -m formauto
```

## How to Use in Code

### Old Way (Still Works)
```python
from wowauto import SequenceRunner
runner = SequenceRunner()
runner.load_file("sequences.json")
runner.run_forever()
```

### New Way (More Options)
```python
# Import specific components
from wowauto import SequenceRunner, ActionExecutor, WindowDetector

# Use just the executor
executor = ActionExecutor(dry_run=False)
action = {"type": "key", "action": "press", "key": "w"}
await executor.execute_action(action)

# Use just the loader
from wowauto import SequenceLoader
loader = SequenceLoader()
sequences = loader.load_file("myfile.json")
```

## What's Better?

### Before
- **2 huge files** (559 and 536 lines)
- Hard to find specific code
- Difficult to test individual parts
- Everything tightly coupled

### After
- **10+ focused modules** (50-300 lines each)
- Clear responsibility for each file
- Easy to test components independently
- Modular and reusable

## Dependencies

Already cleaned up - only essential packages:
```
pyinstaller==5.13.0
pillow==9.5.0
requests==2.31.0
urllib3==1.26.16
pywin32==306
keyboard==0.13.5
mouse==0.7.1
pynput==1.7.6
```

No AI/ML packages (numpy, opencv, torch removed as requested).

## Need Help?

- **Full details**: Read `REFACTORING.md`
- **API docs**: Check docstrings in each module
- **Examples**: See `wowauto/__main__.py` and `formauto/__main__.py`

## Backward Compatibility

✅ All your existing JSON sequence files work
✅ All your existing scripts work
✅ Settings are preserved in `Documents\wowautopy\`
✅ No breaking changes

The only difference is better code organization!
