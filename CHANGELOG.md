# Changelog

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
