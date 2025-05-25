#!/usr/bin/env python3
import os
import sys
import json
import shutil
import subprocess
import argparse
from pathlib import Path

EXTENSION_ID = "{E6C93316-271E-4b3d-8D7E-FE11B4350AEB}"
HOST_NAME = "always_on_top"
INSTALL_DIR = Path.home() / ".mozilla" / "native-messaging-hosts"
MANIFEST_PATH = INSTALL_DIR / f"{HOST_NAME}.json"
SCRIPT_NAME = f"{HOST_NAME}.py"
COMPILED_NAME = f"{HOST_NAME}.bin"
BUILD_DIR = INSTALL_DIR / "build"
SCRIPT_PATH = BUILD_DIR / SCRIPT_NAME
COMPILED_PATH = BUILD_DIR / COMPILED_NAME
FINAL_BIN_PATH = INSTALL_DIR / COMPILED_NAME
LOG_FILE = Path("/tmp") / f"{HOST_NAME}.log"

DEBUG = True
args = None  # Will be populated via argparse

def log(*a):
    if not a:
        message = ""
    else:
        message = "[DEBUG] " + " ".join(str(x) for x in a)
    try:
        if message or LOG_FILE.is_file():
            with open(LOG_FILE, "a") as f:
                f.write(message + "\n")
    except Exception as e:
        if DEBUG:
            print(f"⚠️ Failed to write log: {e}")

    if DEBUG:
        if message or LOG_FILE.is_file():
            print(message)

def error_exit(message):
    print(f"❌ {message}", file=sys.stderr)
    sys.exit(1)

def check_dependencies():
    for tool in ("xdotool", "wmctrl"):
        if shutil.which(tool) is None:
            error_exit(f"Missing required tool: {tool}. Please install it.")

def install_manifest(compiled_path):
    INSTALL_DIR.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": HOST_NAME,
        "description": "Always on Top",
        "path": str(compiled_path),
        "type": "stdio",
        "allowed_extensions": [EXTENSION_ID]
    }
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=4)
    log(f"✅ Installed manifest at {MANIFEST_PATH}")

def write_self_to(script_target):
    src = Path(__file__).resolve()
    if script_target.resolve() != src:
        BUILD_DIR.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, script_target)
        log(f"✅ Script copied to {script_target}")

def compile_with_nuitka():
    log("⚙️ Compiling script using Nuitka...")
    venv_path = BUILD_DIR / "venv"
    pip = venv_path / "bin" / "pip"
    python = venv_path / "bin" / "python"

    if not venv_path.exists():
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)

    subprocess.run([str(pip), "install", "--upgrade", "pip", "nuitka"], check=True)

    build_args = [
        str(python), "-m", "nuitka",
        "--assume-yes-for-downloads",
    ]

    if args.onefile:
        build_args += ["--onefile", "--output-filename=" + COMPILED_NAME]
    else:
        build_args += ["--standalone", "--output-dir=" + str(BUILD_DIR)]

    build_args.append(str(SCRIPT_PATH))
    subprocess.run(build_args, check=True)

    if args.onefile:
        if not COMPILED_PATH.exists():
            error_exit("❌ Compilation failed.")
        else:
            copy_compiled_to_final()
            log(f"✅ Copied Compiled onefile binary {FINAL_BIN_PATH}")

    else:
        # In standalone mode, binary goes inside `.dist/`
        dist_dir = BUILD_DIR / (SCRIPT_PATH.stem + ".dist")
        binary_path = dist_dir / COMPILED_NAME
        if not binary_path.exists():
            error_exit("❌ Standalone compilation failed.")
        if FINAL_BIN_PATH.is_file():
            FINAL_BIN_PATH.remove()
        shutil.copytree(dist_dir, FINAL_BIN_PATH, dirs_exist_ok=True)
        log(f"✅ Copied standalone bundle to {FINAL_BIN_PATH}")

def copy_compiled_to_final():
    if FINAL_BIN_PATH.is_dir():
        shutil.rmtree(FINAL_BIN_PATH, ignore_errors=True)
    shutil.copy2(COMPILED_PATH, FINAL_BIN_PATH)
    log(f"✅ Copied binary to {FINAL_BIN_PATH}")

def is_installed():
    if args.onefile:
        return FINAL_BIN_PATH.exists() and MANIFEST_PATH.exists()
    else:
        return FINAL_BIN_PATH.exists() and FINAL_BIN_PATH.is_dir() and MANIFEST_PATH.exists()

def cleanup():
    log("🧹 Deleting build folder...")
    shutil.rmtree(BUILD_DIR, ignore_errors=True)

def setup():
    check_dependencies()

    if args.force or not is_installed():
        write_self_to(SCRIPT_PATH)
        if not getattr(sys, 'frozen', False):
            compile_with_nuitka()
        else:
            # Already compiled — need to copy self or dist folder
            if args.onefile:
                # Copy the current binary to FINAL_BIN_PATH
                if FINAL_BIN_PATH.is_dir():
                    shutil.rmtree(FINAL_BIN_PATH, ignore_errors=True)
                shutil.copy2(Path(sys.executable), FINAL_BIN_PATH)
                log(f"✅ Copied onefile binary to {FINAL_BIN_PATH}")
            else:
                # We're in standalone mode — copy the entire folder
                dist_dir = Path(sys.executable).parent
                if FINAL_BIN_PATH.is_file():
                    FINAL_BIN_PATH.remove()
                shutil.copytree(dist_dir, FINAL_BIN_PATH, dirs_exist_ok=True)
                log(f"✅ Copied standalone bundle to {FINAL_BIN_PATH}")

        exec_path = str(FINAL_BIN_PATH if args.onefile else FINAL_BIN_PATH / COMPILED_NAME)
        install_manifest(exec_path)

        if not args.keepbuild:
            cleanup()
        else:
            log("🧪 Keeping build folder for inspection")

        log("✅ Installation complete.")
        os.execv(exec_path, [exec_path])
    else:
        log("✅ Already installed.")

def toggle_window_on_top():
    try:
        log("🟢 Getting window under mouse")
        loc = subprocess.run(["xdotool", "getmouselocation", "--shell"], capture_output=True, text=True)
        win_id = None
        for line in loc.stdout.splitlines():
            if line.startswith("WINDOW="):
                win_id = line.split("=")[1].strip()
                break
        if not win_id:
            return
        subprocess.run(["wmctrl", "-i", "-r", win_id, "-b", "toggle,above"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["xdotool", "windowraise", win_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        log(f"✅ Toggled always-on-top for window ID {win_id}")
    except Exception as e:
        log(f"❌ Error: {e}")

def read_native_message():
    raw_length = sys.stdin.buffer.read(4)
    if not raw_length:
        return None
    message_length = int.from_bytes(raw_length, byteorder='little')
    message = sys.stdin.buffer.read(message_length).decode("utf-8")
    return json.loads(message)

def send_native_message(message):
    encoded = json.dumps(message).encode("utf-8")
    sys.stdout.buffer.write(len(encoded).to_bytes(4, byteorder="little"))
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--standalone", dest="onefile", action="store_false", help="Compile as standalone binary (not working right now)")
    parser.add_argument("--force", action="store_true", help="Force recompile and reinstall")
    parser.add_argument("--keepbuild", action="store_true", help="Keep build folder after install")
    return parser.parse_args()

def main():
    log()
    log("🟢 Log is at " + str(LOG_FILE))
    global args
    args = parse_args()
    log("🟢 Script started with args:", sys.argv)

    if not is_installed() or args.force:
        log("🔧 Triggering setup()")
        setup()
        return  # execv already happened

    if not sys.stdin.isatty():
        log("💬 Native message input detected")
        msg = read_native_message()
        toggle_window_on_top()
        send_native_message({ "status": "ok" })
    else:
        log("🖱️  CLI/manual invocation")
        toggle_window_on_top()

if __name__ == "__main__":
    main()
