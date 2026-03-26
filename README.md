<div align="center">

```text
██████╗  █████╗ ███╗   ██╗ ██████╗ ███████╗███╗   ██╗
██╔══██╗██╔══██╗████╗  ██║██╔════╝ ██╔════╝████╗  ██║
██████╔╝███████║██╔██╗ ██║██║  ███╗█████╗  ██╔██╗ ██║
██╔══██╗██╔══██║██║╚██╗██║██║   ██║██╔══╝  ██║╚██╗██║
██████╔╝██║  ██║██║ ╚████║╚██████╔╝███████╗██║ ╚████║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝
```

**Terminal ASCII banner generator — because plain text is boring.**

[![License](https://img.shields.io/github/license/programmersd21/bangen?style=for-the-badge&color=cyan)](LICENSE)
[![Stars](https://img.shields.io/github/stars/programmersd21/bangen?style=for-the-badge&color=yellow)](https://github.com/programmersd21/bangen/stargazers)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

</div>

## ✨ Screenshot

![Screenshot](screenshot.png)

---

## ⌛ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=pro-grammer-sd/bangen&type=Date)](https://star-history.com/#pro-grammer-sd/bangen&Date)

---

## ▶️ Demonstration

👆 Click the picture below to watch the demo (redirects to YouTube)

<p align="center">
  <a href="https://youtu.be/QaXEEHgKrUg">
    <img src="https://img.youtube.com/vi/QaXEEHgKrUg/0.jpg" alt="Demo video" width="720">
  </a>
</p>

---

## 🎨 What is Bangen?

**Bangen** is a colorful, animated terminal banner generator built on [`pyfiglet`](https://github.com/pwaller/pyfiglet) and [`rich`](https://github.com/Textualize/rich). Type a word, pick a font and a color, and watch your terminal come alive with big bold ASCII art — optionally animated, optionally saved.

No config files. No setup ceremony. Just run and render.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🖋️ **Multiple Fonts** | Choose from a curated preset list or type any `pyfiglet` font name |
| 🌈 **Five Colors** | `cyan` · `red` · `green` · `yellow` · `magenta` |
| 📦 **Panel Display** | Clean bordered panel with optional title via `rich` |
| 🎞️ **Line Animation** | Optional line-by-line reveal for dramatic effect |
| 💾 **Save to File** | Export your banner to a `.txt` file instantly |
| 💬 **Interactive Prompts** | Clear, guided terminal UI — no arguments needed |

---

## 🛠️ Requirements

- 🐍 Python **3.9+**

---

## 🚀 Installation

```bash
# Clone the repo
git clone https://github.com/programmersd21/bangen.git
cd bangen

# Set up a virtual environment
python -m venv .venv
.\.venv\Scripts\activate   # Windows
# source .venv/bin/activate  # Linux / macOS

# Install
pip install .
# Or, for development:
# pip install -e .
```

---

## ▶️ Usage

```bash
bangen
```

Bangen will walk you through everything interactively — text, font, color, animation, and save options. No flags, no config. Just vibes.

---

## 🖼️ Example Output

```text
██████╗  █████╗ ███╗   ██╗ ██████╗ ███████╗███╗   ██╗
██╔══██╗██╔══██╗████╗  ██║██╔════╝ ██╔════╝████╗  ██║
██████╔╝███████║██╔██╗ ██║██║  ███╗█████╗  ██╔██╗ ██║
██╔══██╗██╔══██║██║╚██╗██║██║   ██║██╔══╝  ██║╚██╗██║
██████╔╝██║  ██║██║ ╚████║╚██████╔╝███████╗██║ ╚████║
╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝
```

*Rendered above: `BANGEN` in `ansi_shadow` font, `cyan` color, inside a `rich` panel.*

---

## 🗂️ Project Layout

```
bangen/
├── 🐍 bangen.py          # Main application
├── 📦 pyproject.toml     # Packaging + dependencies
├── 📄 LICENSE            # MIT license
├── 🙈 .gitignore         # Python defaults
├── 💁‍♂️ README.md          # Project information
├── 🌟 demo.mp4           # A demonstration of the app
└── 📸 screenshot.png     # A screenshot of the app
```

---

## 💡 Tips

> 🔠 Want more fonts? When prompted for a font, type **any valid `pyfiglet` font name** directly.
> Explore the full list with:
> ```python
> import pyfiglet
> print(pyfiglet.FigletFont.getFonts())
> ```

---

## 📜 License

MIT — do whatever you want with it. See [`LICENSE`](LICENSE) for the legal bits.

---

<div align="center">
Made with 🖤 and too much terminal time · <a href="https://github.com/programmersd21">programmersd21</a>
</div>
