# 🦸‍♂️ Marvel Avengers Hanging Animations for Windows 10/11

A lightweight, transparent desktop overlay application for Windows 10 and 11 featuring 100+ hanging Marvel and Avengers-themed character icons, objects, weapons, and cosmic energy effects with natural pendulum swinging physics, particle effects, and mouse interaction.

---

## 🌟 Key Features

- **100+ Unique Animation Presets**:
  - **Avengers Core**: Captain America Shield, Thor Mjolnir & Stormbreaker, Iron Man Helmet & Arc Reactor, Black Widow Emblem, Hawkeye Target, Ant-Man & Wasp, Vision Mind Gem, Falcon Wings, War Machine, Rescue.
  - **Cosmic & Infinity**: Space, Mind, Reality, Power, Time, Soul Stones, Infinity Gauntlet (Open & Fist), Tesseract, Captain Marvel Star, Eternals Celestial Symbol.
  - **Spider-Verse**: Classic Web-Slinger, Miles Morales Black/Red, Spider-Gwen, Iron Spider, Spider-Man 2099, Stark Web Shooter, Spider-Sense ring.
  - **Mystic & Magic**: Doctor Strange Tao Mandala Portal, Eldritch Shield, Scarlet Witch Hex Crest, Eye of Agamotto, Darkhold Rune, Agatha Purple Magic, Wiccan Spell Core.
  - **Wakanda & Asgard**: Black Panther Vibranium Mask & Tooth Necklace, Shuri Sonic Gauntlet, Loki Horned Helmet, Heimdall Bifrost Sword, Valkyrie Pegasus Crest, Hela Crown.
  - **Villains & Artifacts**: Thanos Double Blade, Ultron Prime Red Core, Hydra Crimson Emblem, Ronan Cosmi-Rod, Taskmaster Shield, Kang Time Orb, Gorr Necrosword.
  - **Guardians & Galactic**: Star-Lord Lenses, Baby Groot Twig Rune, Rocket Plasma Cannon, Gamora God-Slayer, Drax Daggers, Yondu Yaka Arrow, Nova Corps Starburst.

- **Natural Pendulum Physics & Tethers**:
  - Realistic swinging math, gravity, damping, and mass coefficients.
  - Multiple tether styles: Metal Chains, Spider Webs, Energy Lasers, Bifrost Beams, Magic Wisps, Strings & Ropes.

- **Interactive Mouse Effects**:
  - **Drag & Drop**: Click and swing items across the screen.
  - **Hovering**: Triggers excitement pulse, speed boost, and particle glow.
  - **Click Special Effects**:
    - ⚡ *Thor Lightning Bolt Strike*
    - 🚀 *Iron Man Repulsor Blast*
    - 🕸️ *Spider Web Spray*
    - 🔮 *Doctor Strange Mandala Portal Spin*
    - 🌌 *Thanos Infinity Snap Disintegration Flash*
    - 🪄 *Scarlet Witch Chaos Hex Field*
    - 🟣 *Wakanda Vibranium Shockwave*
    - 🟢 *Hulk Gamma Sonic Clap*

- **Futuristic Dark Control Panel**:
  - Start/Pause Overlay
  - Animation Speed Slider (0.2x to 3.0x)
  - Active Objects Count (1 to 30)
  - Transparency Adjustment (20% to 100%)
  - Randomize & Reset
  - Real-time Search & Category Filters across 100+ Presets
  - Toggle Individual Presets on the fly

- **Performance & System Integration**:
  - 60 FPS smooth rendering loop via PyQt6.
  - Low CPU usage with Win32 click passthrough.
  - Windows System Tray Support.
  - Press `ESC` to focus Control Panel.

---

## 🛠️ Requirements & Installation

1. **Python 3.10+**
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## 🚀 How to Run

Launch the application directly with Python:
```bash
python main.py
```

---

## 📦 How to Build Standalone Executable (`MarvelAvengersHanging.exe`)

Run the automated build script:
```cmd
build.bat
```

Or run PyInstaller manually:
```cmd
pyinstaller --noconfirm --onedir --windowed --name "MarvelAvengersHanging" --add-data "animations;animations" --add-data "ui;ui" --add-data "assets;assets" main.py
```

The compiled standalone application will be located inside the `dist/` directory as `MarvelAvengersHanging.exe`.

---

## 🎨 Adding Custom Images

To use custom PNG/SVG artwork instead of procedural vector shapes, simply drop transparent PNG files into the `assets/` folder. The app will seamlessly detect and attach them to swinging tethers!

---

## 📄 License
Created for personal desktop customization. All vector graphics are original procedurally generated artwork.
