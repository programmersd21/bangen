# Changelog

## [2.2.0]

### Added
- `--screensaver` full-screen terminal mode with auto-fitted banner sizing, randomized scene rotation, effect mixing, and optional seed/duration controls
- Screensaver font rotation across multiple safe fitted fonts per scene
- Expanded README documentation for screensaver mode and refreshed presentation details

### Changed
- Refined the README structure and GitHub presentation, including more deliberate visual emphasis

### Fixed
- Screensaver scene generation now skips invalid randomized effect kwargs instead of breaking playback
- Screensaver fitting now reserves extra margin for motion/distortion-heavy scenes so text stays on-screen
- Screensaver font selection is randomized across safe fits instead of collapsing into one repeated choice

## [2.1.0]

### Added
- `--preset-file` support in the CLI for loading a preset JSON from any path without saving it
- TUI preset loader modal with support for loading saved presets or an arbitrary preset file
- Expanded README documentation for preset authoring, preset loading, and current CLI/TUI workflows

### Changed
- Reworked the active effect library for more stable, bounded, export-safe motion, distortion, visual, and signature rendering
- Improved GIF and PNG raster rendering with better font metrics, larger raster sizing, and shared GIF palette generation across sampled frames
- Refined `flicker` and `glitch` behavior to reduce export fuzziness and palette churn

### Fixed
- `wipe` now reveals visible content bounds instead of wasting progress on indentation
- Preset-derived `gradient_direction` is preserved unless explicitly overridden on the CLI
- Windows console export status output now uses ASCII arrows to avoid `cp1252` encoding crashes

## [2.0.0]

### Added
- Modular architecture: `rendering`, `gradients`, `effects`, `tui`, `cli`, `export`, `presets`, `ai`
- True-colour RGB gradient engine with multi-stop interpolation (`Gradient`)
- Composable effect pipeline on the `Banner` object
- Effects: Wave, Glitch, Pulse (brightness oscillation), Typewriter, Scroll
- Full-screen interactive TUI with split controls/preview layout (`TUIApp`)
- Full CLI via `argparse` with all features accessible from the terminal
- JSON preset system stored in `~/.bangen/presets/` (8 built-in presets)
- Multi-format export: TXT, HTML (inline styles), PNG, animated GIF
- External FIGlet font loading via `--font-dir`
- AI rule-based prompt-to-style suggester

### Changed
- Minimum Python version raised to 3.11
- `pyfiglet` and `rich` remain the only required dependencies
- `Pillow` is now an optional dependency (`pip install bangen[images]`)

### Removed
- Monolithic single-file `bangen.py` replaced by package

## [0.1.0]

- Initial release: interactive prompts, 5 named colours, line-by-line animation, TXT save
