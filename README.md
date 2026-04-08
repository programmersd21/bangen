# Bangen ✨

![App Banner](demo/app_banner.gif)

**Bangen** is an ASCII banner renderer built on `pyfiglet`, `rich`, and `Pillow`.
It gives you a fast live **TUI**, a composable effect pipeline, JSON presets, and export support for `TXT`, `PNG`, `GIF`, and `HTML`.

Built for terminal art, title cards, intros, and animated text that still feels sharp when exported.

![Screenshot](demo/screenshot.png)

## Why It Stands Out ⚡

- Live split-screen TUI with export modal
- Static and animated banner rendering
- Transparent `PNG` and animated transparent `GIF` export
- Plain `TXT` export with exact ASCII output
- Multi-stop gradients with horizontal or vertical interpolation
- Built-in presets plus user presets stored in `~/.bangen/presets/`
- Effect library grouped into motion, visual, temporal, distortion, and signature tiers
- CLI workflows for rendering, exporting, listing assets, and loading presets

## Quick Look 👀

```bash
bangen "SYSTEM READY" --font slant --gradient "#7c3aed:#06b6d4" --effect glow --effect wave
```

## Setup 🛠️

```bash
git clone https://github.com/pro-grammer-SD/bangen.git
cd bangen
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Requirements:

- Python `3.11+`
- Pillow is included in the base install

## Quick Start 🚀

Render a basic banner:

```bash
bangen "HELLO"
```

Render with custom styling:

```bash
bangen "HELLO" --font slant --gradient "#ff00ff:#00ffff"
```

Render with effects:

```bash
bangen "HELLO" --effect wave --effect glow --effect pulse --speed 1.5 --amplitude 2.0
```

Run screensaver mode:

```bash
bangen "HELLO" --screensaver
```

Export a GIF:

```bash
bangen "HELLO" --effect wave --effect glow --export-gif banner.gif --gif-duration 3 --gif-fps 20
```

## Interface 🎛️

### TUI 🖥️

Launch the editor:

```bash
bangen
```

Controls:

- `↑↓` navigate fields and effects
- `←→` adjust font or numeric settings
- `Enter` edit or toggle the selected field
- `l` load a saved preset or load from a custom preset file
- `e` open the export dialog
- `s` save the current preset
- `q` quit

The effect selector is windowed, so you can move through the full library without overflowing the controls panel.

### Export Dialog 📦

Press `e` inside the TUI to open the exporter.

- Toggle `GIF`, `PNG`, and `TXT`
- Edit the output path directly
- Adjust GIF-only `duration` and `fps`
- Auto-update the file extension when the format changes
- Confirm overwrite when the target file already exists

### CLI ⌨️

#### Basic Rendering

```bash
bangen "HELLO"
bangen "HELLO" --font slant --gradient "#ff00ff:#00ffff"
bangen "HELLO" --gradient "#ff0000:#ffff00:#00ff00" --gradient-dir vertical
```

#### Discoverability

```bash
bangen --list-effects
bangen --list-fonts
bangen --list-presets
```

#### Presets and AI

```bash
bangen --preset cyberpunk "HELLO"
bangen --preset matrix "SYSTEM"
bangen --preset-file ./my_preset.json "HELLO"
bangen "HELLO" --ai "retro CRT hacker title"
```

#### Export

```bash
bangen "HELLO" --export-txt banner.txt
bangen "HELLO" --export-png banner.png
bangen "HELLO" --effect wave --effect glow --export-gif banner.gif --gif-duration 3 --gif-fps 20
bangen "HELLO" --export-html banner.html
```

#### Screensaver

Turns any banner text into a full-terminal animated screensaver. It auto-fits the text to the current terminal size, switches between effect scenes, and randomizes speed, amplitude, frequency, and scene duration.

```bash
bangen "SYSTEM READY" --screensaver
bangen "NIGHT MODE" --screensaver --screensaver-duration 60
bangen "SIGNAL" --screensaver --screensaver-seed 42
```

Notes:

- `Ctrl+C` exits screensaver mode
- `--font`, `--gradient`, presets, and AI prompts still influence the starting style
- effect selection is managed by the screensaver engine, so `--effect` is not the main control surface in this mode
- export flags are ignored while screensaver mode is running

#### Terminal Animation

Useful for temporal effects such as `wipe` and `typewriter`:

```bash
bangen "HELLO" --effect wipe --animate --animate-duration 5
```

## Effects Library 🎨

### Motion

- `wave`
- `vertical_wave`
- `bounce`
- `scroll`
- `drift`
- `shake`

### Visual

- `gradient_shift`
- `pulse`
- `rainbow_cycle`
- `glow`
- `flicker`
- `scanline`

### Temporal

- `typewriter`
- `fade_in`
- `wipe`
- `stagger`
- `loop_pulse`

### Distortion

- `glitch`
- `chromatic_aberration`
- `noise_injection`
- `melt`
- `warp`
- `fragment`

### Signature

- `matrix_rain`
- `fire`
- `electric`
- `vhs_glitch`
- `neon_sign`
- `wave_interference`
- `particle_disintegration`

## Effect Stacks 🧪

Effects are order-sensitive and composable:

```python
banner.apply(build_effect("wave", config=cfg))
banner.apply(build_effect("chromatic_aberration", config=cfg))
banner.apply(build_effect("pulse", config=cfg))
```

Common style stacks:

- `cyberpunk`: `glitch` + `chromatic_aberration` + `pulse`
- `neon`: `glow` + `pulse` or `neon_sign`
- `matrix`: `matrix_rain` + `typewriter`
- `retro`: `scanline` + `flicker`
- `fire`: `fire` + `melt`
- `electric`: `electric` + `glow`

## Styling & Presets 🌈

### Gradients

Use colon-separated hex stops:

```text
#ff00ff:#00ffff
#ff0000:#ffff00:#00ff00
```

Use `--gradient-dir vertical` for top-to-bottom interpolation.

### Presets 💾

#### Storage

Saved presets live under:

```text
~/.bangen/presets/*.json
```

You can create these files manually, save them from the TUI with `s`, or save from the CLI with `--save-preset NAME`.

#### Loading

- TUI: press `l`, then choose `SAVED` or `FILE`
- CLI: `--preset NAME` loads from built-ins or `~/.bangen/presets/`
- CLI: `--preset-file PATH` loads a preset JSON from any path without saving it

#### Preset Format

```json
{
  "name": "my_preset",
  "font": "ansi_shadow",
  "gradient": "#ff00ff:#00ffff",
  "gradient_direction": "horizontal",
  "effects": ["wave", "glow", "pulse"],
  "effect_config": {
    "wave": { "speed": 1.8, "amplitude": 2.0, "frequency": 0.7 },
    "pulse": { "speed": 1.2, "min_brightness": 0.55 },
    "glow": {}
  }
}
```

Notes:

- `name`, `font`, and `gradient` should always be provided
- `effects` order matters
- `speed`, `amplitude`, and `frequency` map to shared `EffectConfig`
- any additional keys inside `effect_config` are passed to the effect constructor

## Project Layout 🧱

```text
bangen/
├── effects/
│   ├── base.py
│   ├── distortion.py
│   ├── motion.py
│   ├── signature.py
│   ├── temporal.py
│   ├── utils.py
│   └── visual.py
├── export/
│   ├── exporter.py
│   ├── gif.py
│   ├── png.py
│   └── txt.py
├── gradients/
├── presets/
├── rendering/
└── tui/
    ├── app.py
    ├── export_dialog.py
    └── preset_dialog.py
```

## Notes 📝

- Animated exports look best when you keep effect stacks readable instead of maxing out distortion-heavy combinations.
- Temporal effects such as `wipe` and `typewriter` are best previewed with `--animate` in the terminal before exporting.
- `--screensaver` is designed for live terminal playback, not export generation.

## License 📄

MIT. See [LICENSE](LICENSE).
