# 🎨 WoW Auto - New GUI Theme

## Beautiful Brown/Gold WoW-Inspired Design

Your GUI has been completely redesigned with a stunning World of Warcraft-inspired theme featuring:

### 🎯 Color Scheme

**Primary Colors:**
- **Dark Brown** (`#2b1f14`) - Main background, immersive and easy on eyes
- **Medium Brown** (`#3d2a1f`) - Section containers
- **Light Brown** (`#4d3a2a`) - Input fields and status boxes
- **Gold** (`#d4af37`) - Primary accent, WoW signature color
- **Light Gold** (`#f0d98c`) - Headers and highlights
- **Beige Text** (`#f0e6d2`) - Main text, high readability

**Status Colors:**
- **Success Green** (`#4ade80`) - Running status
- **Error Red** (`#ef4444`) - Stopped/error status
- **Warning Orange** (`#fb923c`) - Alerts

### ✨ New Features

#### 1. **Rounded Buttons**
- Custom `RoundedButton` class with 8px radius corners
- Smooth hover effects (color transitions)
- Hand cursor on hover
- Gold → Lighter Gold hover animation

#### 2. **Elegant Header**
- ⚔️ Sword icons for WoW feel
- Large title with gold color
- Subtitle for context
- Gradient-like background effect

#### 3. **Section Organization**
```
📁 Sequence File
   - Styled input field with Consolas font
   - Rounded browse button

📂 Load Sequences
   - Clear call-to-action button

📋 Available Sequences
   - Dark themed listbox
   - Gold selection highlight
   - Custom scrollbar

⚙️ Configuration
   - 🎯 Global toggle key input
   - Centered, bold key display

📊 Status
   - 🤖 Automation status (with emoji)
   - ⚡ Runner thread status
   - 🎧 Listener status
   - Color-coded indicators
```

#### 4. **Action Buttons**
- **Large START/STOP button** (200x45px)
  - Green when stopped → "▶️ START AUTOMATION"
  - Red when running → "⏸️ STOP AUTOMATION"
  - Dynamic color switching
  
- **Bottom control buttons:**
  - 💾 Save (brown/gold theme)
  - 💾 Save & Exit (brown/gold theme)
  - ❌ Quit (red danger button)

#### 5. **Status Bar**
- Bottom status message display
- Muted text color
- Professional appearance

#### 6. **Enhanced Stop Window**
- Larger (140x60px) for better visibility
- Rounded corners matching main theme
- Hover effect (darker red)
- ⏹️ Stop icon with text
- Always on top-right corner

### 🎮 Typography

**Fonts Used:**
- **Segoe UI** - Modern, clean Windows font
  - Headers: Bold, 16pt (title), 10pt (sections)
  - Body: Regular, 9-10pt
- **Consolas** - Monospace for file paths and keys
  - File paths: 9pt
  - Hotkey display: 10pt bold

### 📐 Layout Improvements

**Before:**
- Basic grid layout
- Standard tkinter widgets
- Plain white/gray theme
- No visual hierarchy

**After:**
- Organized sections with clear headers
- Custom rounded buttons
- WoW color palette throughout
- Clear visual hierarchy with spacing
- Icon usage (📁📂📋⚙️📊🤖⚡🎧💾❌▶️⏸️⚔️)

### 🖱️ Interactive Elements

#### Hover Effects:
- **Buttons**: Color darkens/brightens on hover
- **Cursor**: Changes to hand pointer over clickable elements
- **Stop Window**: Red → Darker red transition

#### Dynamic Updates:
- **Start/Stop button**: Text and color change with state
- **Status labels**: Color-coded (green=running, red=stopped)
- **Real-time status**: Thread and listener monitoring

### 💻 Technical Implementation

```python
# Custom RoundedButton class
- Canvas-based drawing
- Arc corners for smooth curves
- Event binding for clicks and hovers
- Dynamic redrawing on state change

# Color constants
COLORS dictionary for consistency
- Easy to modify theme
- Centralized color management

# Frame organization
- Nested frames for sections
- Consistent padding (8-12px)
- Strategic spacing for visual flow
```

### 🚀 Usage

Simply run your GUI as before:

```bash
# Using test.bat (recommended)
test.bat

# Or directly
python formauto.py

# Or as module
python -m formauto
```

### 📸 Visual Description

**Window Layout (600x570px):**
```
┌─────────────────────────────────────────────────┐
│  ⚔️ World of Warcraft Automation ⚔️            │ ← Gold header
│     Configure your automation sequences          │
├─────────────────────────────────────────────────┤
│                                                   │
│  📁 Sequence File:                               │
│  ┌─────────────────────────────────────┐ [Browse]│
│  │ path/to/sequence.json               │         │
│  └─────────────────────────────────────┘         │
│                                                   │
│  [📂 Load Sequences]                             │
│                                                   │
│  📋 Available Sequences:                         │
│  ┌─────────────────────────────────────────────┐│
│  │ sequence_1                                   ││
│  │ sequence_2                     ▲             ││
│  │ sequence_3                     █             ││
│  │ sequence_4                     ▼             ││
│  └─────────────────────────────────────────────┘│
│                                                   │
│  ⚙️ Configuration:                               │
│  🎯 Global Toggle Key:  [ F8 ]  [Update]        │
│                                                   │
│  📊 Status:                                      │
│  ┌─────────────────────────────────────────────┐│
│  │ 🤖 Automation: ⏹️ Not Running               ││
│  │ ⚡ Runner: stopped                           ││
│  │ 🎧 Listener: running                         ││
│  └─────────────────────────────────────────────┘│
│                                                   │
│         [  ▶️ START AUTOMATION  ]                │ ← Large green
│                                                   │
│  [💾 Save] [💾 Save & Exit] [❌ Quit]            │
│                                                   │
│  Status message here...                          │ ← Status bar
└─────────────────────────────────────────────────┘
```

### 🎯 Benefits

✅ **Immersive WoW Theme** - Feels like part of the game
✅ **Professional Look** - Modern, polished interface
✅ **Better UX** - Clear visual hierarchy and feedback
✅ **Hover Effects** - Interactive and responsive
✅ **Rounded Design** - Softer, more appealing aesthetic
✅ **Color-Coded Status** - Instant visual feedback
✅ **Icon Usage** - Quick visual recognition
✅ **Better Typography** - Improved readability
✅ **Consistent Spacing** - Clean, organized layout
✅ **Dynamic Buttons** - State changes are obvious

### 🎨 Customization

To change colors, edit the `COLORS` dictionary in `formauto/settings_form.py`:

```python
COLORS = {
    'bg_dark': '#2b1f14',        # Dark background
    'bg_medium': '#3d2a1f',      # Medium background
    'bg_light': '#4d3a2a',       # Light background
    'gold': '#d4af37',           # Gold accent
    'gold_light': '#f0d98c',     # Light gold
    'gold_dark': '#b8942c',      # Dark gold
    'text': '#f0e6d2',           # Main text
    'text_dim': '#c0b49e',       # Dimmed text
    'success': '#4ade80',        # Success green
    'error': '#ef4444',          # Error red
    'warning': '#fb923c',        # Warning orange
}
```

### 🔮 Future Enhancements

Possible additions:
- Animated button transitions
- Progress bars for sequences
- Theme selector (dark/light/classic)
- Transparency effects (Windows 11)
- Custom window icons
- Sound effects on actions
- Minimap-style thumbnail
- Glow effects on active elements

Enjoy your new WoW-themed automation interface! ⚔️✨
