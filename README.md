<div align="center">

```text
██████╗  █████╗ ███╗   ██╗ ██████╗ ███████╗███╗   ██╗
██╔══██╗██╔══██╗████╗  ██║██╔════╝ ██╔════╝████╗  ██║
██████╔╝███████║██╔██╗ ██║██║  ███╗█████╗  ██╔██╗ ██║
██╔══██╗██╔══██║██║╚██╗██║██║   ██║██╔══╝  ██║╚██╗██║
██████╔╝██║  ██║██║ ╚████║╚██████╔╝███████╗██║ ╚████║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝
```

![Screenshot](demo/screenshot.png)

**v2.0 — Premium ASCII rendering engine.**

[![License](https://img.shields.io/github/license/programmersd21/bangen?style=for-the-badge&color=cyan)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue?style=for-the-badge&logo=python)](https://python.org)
[![Version](https://img.shields.io/badge/version-2.0.0-magenta?style=for-the-badge)](CHANGELOG.md)

</div>

---

## What's New in v2.0

Bangen has been completely rewritten from a single-file script into a modular,
Premium ASCII rendering engine.

| Feature | v1 | v2 |
|---|---|---|
| Architecture | Single file | Modular packages |
| Colours | 5 named colours | True-colour RGB gradients |
| Multi-stop gradients | ✗ | ✓ |
| Effect pipeline | Line-by-line reveal | Wave · Glitch · Pulse · Typewriter · Scroll |
| Interactive TUI | Prompt-based | Keyboard-driven split layout |
| CLI | ✗ | Full `argparse` CLI |
| Preset system | ✗ | JSON presets in `~/.bangen/presets/` |
| Export | TXT only | TXT · HTML · PNG · GIF |
| Custom fonts | ✗ | `.flf` font directory scanning |
| AI styling | ✗ | Rule-based prompt-to-banner |
| Python | 3.9+ | 3.11+ |

---

## Installation

```bash
git clone https://github.com/programmersd21/bangen.git
cd bangen
python -m venv .venv && source .venv/bin/activate
pip install -e .
# With image export support:
pip install -e ".[images]"
```

---

## Usage

### Interactive TUI (no arguments)

```bash
bangen
```

Launches a full-screen split-panel TUI:

- **Left panel** — controls: text, font, gradient, effects, speed, amplitude
- **Right panel** — live animated preview
- `↑↓` navigate · `←→` adjust · `Enter` edit/toggle · `s` save preset · `q` quit

### CLI Mode

```bash
# Basic render
bangen "HELLO"

# Custom font and gradient
bangen "HELLO" --font slant --gradient "#ff00ff:#00ffff"

# Multi-stop gradient (vertical)
bangen "HELLO" --gradient "#ff0000:#ffff00:#00ff00" --gradient-dir vertical

# Apply effects
bangen "HELLO" --effect wave --effect pulse --speed 1.5 --amplitude 2.0

# Use a built-in preset
bangen --preset neon_wave "HELLO"
bangen --preset cyberpunk "HACK THE PLANET"
bangen --preset matrix "LOADING"

# AI-driven styling
bangen "HELLO" --ai "cyberpunk neon hacker vibe"
bangen "HELLO" --ai "retro arcade 80s pixel"

# Animated terminal output
bangen "HELLO" --effect wave --animate --animate-duration 8

# Export
bangen "HELLO" --export-txt banner.txt
bangen "HELLO" --export-html banner.html --gradient "#ff00ff:#00ffff"
bangen "HELLO" --export-png banner.png --gradient "#ff0000:#ff8800:#ffff00"
bangen "HELLO" --effect pulse --export-gif banner.gif --gif-duration 3 --gif-fps 20

# Save / list presets
bangen "HELLO" --font doom --gradient "#ff6600:#ffcc00" --save-preset my_retro
bangen --list-presets
bangen --list-fonts

# Pipeline-friendly (no border)
bangen "DEPLOY" --no-border --static | cat
```

---

## Architecture

```
bangen/
├── main.py                    # Entry point
├── pyproject.toml
├── bangen/
│   ├── rendering/
│   │   ├── engine.py          # RenderEngine — pyfiglet wrapper + font discovery
│   │   └── banner.py          # Banner — composable effect pipeline
│   ├── gradients/
│   │   └── gradient.py        # Gradient — multi-stop RGB interpolation
│   ├── effects/
│   │   ├── base.py            # Effect, EffectConfig, BrightnessModifier
│   │   ├── wave.py            # Sin-based horizontal offset
│   │   ├── glitch.py          # Stochastic character substitution
│   │   ├── pulse.py           # Brightness oscillation
│   │   ├── typewriter.py      # Char-by-char reveal
│   │   └── scroll.py          # Horizontal banner scroll
│   ├── tui/
│   │   └── app.py             # TUIApp — rich.Live split-panel UI
│   ├── cli/
│   │   ├── parser.py          # argparse definitions
│   │   └── runner.py          # CLI command handler
│   ├── export/
│   │   └── exporter.py        # TXT · HTML · PNG · GIF
│   ├── presets/
│   │   └── manager.py         # Built-in + user JSON presets
│   └── ai/
│       └── suggester.py       # Prompt-to-style rule engine
```

---

## Built-in Presets

| Preset | Font | Gradient | Effects |
|---|---|---|---|
| `neon_wave` | ansi_shadow | magenta→cyan | wave, pulse |
| `cyberpunk` | slant | pink→yellow→green | glitch |
| `matrix` | banner3-D | dark→bright green | typewriter |
| `retro` | doom | orange→yellow | — |
| `ocean` | speed | navy→blue→cyan | wave |
| `vaporwave` | small | pink→purple→blue | scroll, pulse |
| `electric` | ansi_shadow | blue→cyan→white | glitch, pulse |
| `fire` | block | red→orange→yellow | wave, glitch |

---

## Custom Fonts

Place any `.flf` FIGlet font file in a directory and pass it with `--font-dir`:

```bash
bangen "HELLO" --font-dir ~/my-fonts --font myfont
```

---

## Gradient Format

Gradients are colon-separated hex colour stops:

```
"#ff0000:#ffff00:#00ff00"   # red → yellow → green (3 stops)
"#ff00ff:#00ffff"           # magenta → cyan (2 stops)
```

Horizontal (default) varies colour left-to-right per line.  
Vertical (`--gradient-dir vertical`) varies colour top-to-bottom.

---

## Requirements

- Python **3.11+**
- `pyfiglet`, `rich`
- `Pillow` (optional — PNG/GIF export only)

---

## License

MIT — see [LICENSE](LICENSE).

---

<div align="center">
Made with 🖤 and too much terminal time · <a href="https://github.com/programmersd21">programmersd21</a>
</div>
