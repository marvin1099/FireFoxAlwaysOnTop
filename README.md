# 🖱️ Firefox Always On Top

This is a native messaging host that allows the Firefox extension:  
https://addons.mozilla.org/en-US/firefox/addon/always-on-top/  
to toggle the "Always on Top" state,  
for any window currently under your mouse cursor, but for Linux.

The original for Windows is here:  
https://github.com/vm-devr/aot

The code from the original is also here in this repo.  
The only files I added are:
- README.md
- LICENSE
- FireFoxAlwaysOnTop.py

## 🔧 Prerequisites

Ensure the following tools are installed on your system:

- [`xdotool`](https://github.com/jordansissel/xdotool)
- [`wmctrl`](https://gitlab.com/rstankov/wmctrl)

You can typically install them via your package manager:

```bash
sudo apt install xdotool wmctrl  # Debian/Ubuntu
sudo pacman -S xdotool wmctrl    # Arch
````

---

## 🚀 Installation

### ✅ Precompiled Binary

You can find the latest precompiled **onefile** binary in the [Releases](https://codeberg.org/marvin1099/FireFoxAlwaysOnTop) section.  
Just download it and run:

```bash
./always_on_top.bin
```

This will install the native messaging host and set up everything automatically.

---

### 🛠️ Build It Yourself

You can also build and install the host yourself. Simply run:

```bash
python3 FireFoxAlwaysOnTop.py
```

This script will:

* Check dependencies
* Compile the binary using [Nuitka](https://nuitka.net/)
* Install the native messaging manifest for Firefox

---

## ⚙️ Optional Flags

* `--force`
  Force recompile and reinstall, even if the binary and manifest already exist.

* `--keepbuild`
  Keep the build folder after compilation for inspection or debugging.

Example:

```bash
python3 FireFoxAlwaysOnTop.py --force --keepbuild
```

---

## 🧪 How it Works

The extension sends a request to the native host. The host then:

1. Gets the window under the mouse using `xdotool`.
2. Toggles the `_NET_WM_STATE_ABOVE` property using `wmctrl`.
3. Raises the window.

---

## 📁 Files Installed

* The compiled binary is placed in `~/.mozilla/native-messaging-hosts/`
* A manifest JSON is written there to allow Firefox to communicate with the binary

---

## 🐛 Troubleshooting

If it's not working:

* Make sure you're not running Firefox as a **Snap or Flatpak** package (or follow appropriate setup for sandboxed environments).
* Ensure `xdotool` and `wmctrl` are working from the terminal.
* Try running the binary manually to verify it's working outside Firefox.


Keep in mind this is not working as well as on the windows side, but it works.  
Any code contributions are wellcome.  
Notably the pin won't detect if the window is pinned or not.
