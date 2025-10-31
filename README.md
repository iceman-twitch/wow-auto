# WoW Auto & FormAuto Workspace

This workspace contains two automation projects:

## 📁 Project Structure

```
wow-auto/
├── wowauto/                    # WoW sequence automation
│   ├── wowauto.py             # Main sequence runner
│   ├── sequences/             # JSON sequence files
│   │   ├── farming.json
│   │   ├── combat.json
│   │   └── example_sequences.json
│   └── README.md
│
├── wowaiautolearn/            # WoW AI learning system
│   ├── wowaiautolearn.py     # Main AI learning app
│   ├── models/               # Trained AI models
│   ├── screenshots/          # Training screenshots
│   ├── training_data/        # JSON training data
│   └── README.md
│
├── formauto/                  # Form automation (future)
│   ├── formauto.py
│   └── README.md
│
├── shared/                    # Shared utilities
│   ├── __init__.py
│   ├── input_handler.py      # Common input handling
│   └── config.py             # Shared config
│
└── requirements.txt           # All dependencies
```

## 🚀 Quick Start

### WoW Auto (Sequence Runner)
```bash
cd wowauto
python wowauto.py
```

### WoW AI AutoLearn
```bash
cd wowaiautolearn
python wowaiautolearn.py
```

## 📦 Installation

```bash
pip install -r requirements.txt
```

