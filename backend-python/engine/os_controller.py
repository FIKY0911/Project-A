import asyncio
import os
import random
import time
import subprocess
import urllib.parse
import shutil
import re
import platform
from pathlib import Path
from typing import Optional, Tuple, Callable, Dict, Any, List
import pyautogui
import cv2

IS_WINDOWS = platform.system() == "Windows"


from config import FAILSAFE_ENABLED, KEYSTROKE_MIN_INTERVAL, KEYSTROKE_MAX_INTERVAL, DATA_DIR
from guardrails.pii_scanner import PIIScanner
from guardrails.os_protection import OSProtectionGuardrail

pyautogui.FAILSAFE = FAILSAFE_ENABLED
pyautogui.PAUSE = 0.0

class OSAutomationException(Exception):
    def __init__(self, message: str, violation_code: str):
        super().__init__(message)
        self.violation_code = violation_code

def resolve_dynamic_path(target: Optional[str]) -> Optional[Path]:
    """
    Intelligently resolves directories or file paths based on user input.
    Handles fuzzy matches, home folder expansions, conversational prefixes,
    and searches common directories (Documents, Downloads, Desktop, workspace).
    """
    if not target:
        return None

    raw = str(target).strip().strip("'\"`")
    if not raw:
        return None

    # Remove conversational prefixes
    cleaned = re.sub(
        r"^(?:didalam|dalam|di\s+dalam|di|pada|ke|in|inside|into)\s+",
        "",
        raw,
        flags=re.IGNORECASE
    ).strip()
    cleaned = re.sub(
        r"^(?:folder|directory|direktori)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE
    ).strip(" '\"`")

    if not cleaned:
        return None

    if cleaned in (".", "./"):
        return Path.cwd().resolve()

    expanded = Path(cleaned).expanduser()
    if expanded.exists():
        return expanded.resolve()

    home = Path.home()
    cwd = Path.cwd()

    # Base search roots
    search_bases = [
        cwd,
        cwd.parent,
        home / "Documents" / "Latihan Agent" / "JARVIS",
        home / "Documents" / "Latihan Agent",
        home / "Documents",
        home / "Downloads",
        home / "Desktop",
        home / "Pictures",
        home / "Music",
        home / "Videos",
        home,
    ]

    # 1. Direct concatenation with base locations
    for base in search_bases:
        if base.exists():
            candidate = (base / cleaned).resolve()
            if candidate.exists():
                return candidate

    # 2. Case-insensitive exact match of immediate children
    cleaned_lower = cleaned.lower()
    for base in search_bases:
        if base.exists() and base.is_dir():
            try:
                for child in base.iterdir():
                    if child.name.lower() == cleaned_lower:
                        return child.resolve()
            except (PermissionError, OSError):
                continue

    # 3. Recursive directory search (depth 1 to 3)
    for base in [home / "Documents", cwd.parent, home / "Downloads", home / "Desktop"]:
        if base.exists() and base.is_dir():
            try:
                for root, dirs, _ in os.walk(str(base)):
                    try:
                        rel_parts = len(Path(root).relative_to(base).parts)
                    except ValueError:
                        rel_parts = 0
                    if rel_parts > 3:
                        dirs.clear()
                        continue
                    for d in dirs:
                        if d.lower() == cleaned_lower:
                            return (Path(root) / d).resolve()
                        if cleaned_lower in d.lower():
                            return (Path(root) / d).resolve()
            except Exception:
                continue

    # If it looks like an absolute or home path, return expanded path anyway
    if cleaned.startswith("/") or cleaned.startswith("~"):
        return expanded

    return None

class OSController:
    def __init__(self):
        self.snapshots_dir = DATA_DIR / "snapshots"
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)

    async def type_text_humanlike(self, text: str, abort_event: Optional[asyncio.Event] = None, on_char_callback: Optional[Callable] = None):
        """
        Types text with human-like random jitter (20ms - 60ms).
        Checks PII guardrail before typing.
        Checks abort_event after every character for instant kill-switch.
        """
        is_pii, code, matched = PIIScanner.scan(text)
        if is_pii:
            raise OSAutomationException(
                f"PII violation intercepted: {code} ({matched})",
                violation_code=code
            )

        for char in text:
            if abort_event and abort_event.is_set():
                raise asyncio.CancelledError("Typing task aborted by user.")

            pyautogui.write(char)
            if on_char_callback:
                on_char_callback(char)

            jitter = random.uniform(KEYSTROKE_MIN_INTERVAL, KEYSTROKE_MAX_INTERVAL)
            await asyncio.sleep(jitter)

    async def press_key(self, key_name: str):
        pyautogui.press(key_name)

    async def hotkey(self, *keys):
        pyautogui.hotkey(*keys)

    async def move_mouse(self, x: int, y: int, duration: float = 0.3):
        pyautogui.moveTo(x, y, duration=duration)

    async def click(self, x: Optional[int] = None, y: Optional[int] = None, button: str = "left", clicks: int = 1):
        if x is not None and y is not None:
            pyautogui.click(x=x, y=y, clicks=clicks, button=button)
        else:
            pyautogui.click(clicks=clicks, button=button)

    async def scroll(self, clicks: int):
        pyautogui.scroll(clicks)

    async def execute_shell(self, command_str: str) -> Dict[str, Any]:
        """
        Executes terminal command safely under OS guardrail filters.
        """
        # Guardrail checks
        is_bad, code, matched = OSProtectionGuardrail.check_command(command_str)
        if is_bad:
            raise OSAutomationException(f"Destructive shell command prohibited: {matched}", violation_code=code)

        is_pii, pii_code, pii_matched = PIIScanner.scan(command_str)
        if is_pii:
            raise OSAutomationException(f"PII token inside shell command prohibited: {pii_matched}", violation_code=pii_code)

        process = await asyncio.create_subprocess_shell(
            command_str,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return {
            "exit_code": process.returncode,
            "stdout": stdout.decode("utf-8", errors="replace").strip(),
            "stderr": stderr.decode("utf-8", errors="replace").strip()
        }

    async def launch_app(
        self,
        app_name: str,
        path: Optional[str] = None,
        args: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Launches desktop applications dynamically with intelligent name and path resolution.
        Supports passing target directories/files (e.g. opening VSCode or Terminal in a folder).
        """
        name = app_name.lower().strip()
        resolved_path = resolve_dynamic_path(path) if path else None

        # Check if the app_name itself contains arguments or a directory
        parts = app_name.split()
        if len(parts) > 1 and not path:
            base_cand = parts[0].lower()
            rest = " ".join(parts[1:])
            if shutil.which(base_cand) or base_cand in ["code", "vscode", "terminal", "nemo", "nautilus", "files"]:
                name = base_cand
                resolved_path = resolve_dynamic_path(rest) or Path(rest).expanduser()

        # Dynamic mapping of popular applications for Windows vs Linux
        if IS_WINDOWS:
            app_candidates = {
                "browser": ["chrome.exe", "msedge.exe", "firefox.exe"],
                "chrome": ["chrome.exe", "msedge.exe", "firefox.exe"],
                "firefox": ["firefox.exe", "chrome.exe", "msedge.exe"],
                "edge": ["msedge.exe", "chrome.exe"],
                "vscode": ["code.cmd", "code.exe", "code"],
                "code": ["code.cmd", "code.exe", "code"],
                "terminal": ["wt.exe", "powershell.exe", "cmd.exe"],
                "cmd": ["cmd.exe"],
                "powershell": ["powershell.exe"],
                "files": ["explorer.exe"],
                "filemanager": ["explorer.exe"],
                "explorer": ["explorer.exe"],
                "notepad": ["notepad.exe"],
                "calculator": ["calc.exe"],
                "spotify": ["spotify.exe"],
                "music": ["wmplayer.exe", "vlc.exe"],
                "vlc": ["vlc.exe"],
            }
        else:
            app_candidates = {
                "browser": ["google-chrome", "google-chrome-stable", "firefox", "chromium-browser", "chromium", "xdg-open"],
                "chrome": ["google-chrome", "google-chrome-stable", "chromium", "firefox", "xdg-open"],
                "firefox": ["firefox", "google-chrome", "chromium", "xdg-open"],
                "vscode": ["code"],
                "code": ["code"],
                "terminal": ["gnome-terminal", "x-terminal-emulator", "konsole", "xfce4-terminal", "terminator", "tilix", "alacritty", "kitty"],
                "files": ["nemo", "nautilus", "thunar", "dolphin", "pcmanfm", "xdg-open"],
                "filemanager": ["nemo", "nautilus", "thunar", "dolphin", "pcmanfm", "xdg-open"],
                "nemo": ["nemo"],
                "nautilus": ["nautilus"],
                "notepad": ["xed", "gedit", "gnome-text-editor", "mousepad", "kate", "nano"],
                "calculator": ["gnome-calculator", "kcalc", "galculator"],
                "spotify": ["spotify"],
                "music": ["rhythmbox", "vlc", "audacious"],
                "vlc": ["vlc"],
            }

        candidates = app_candidates.get(name, [name])
        found_bin = None
        for bin_name in candidates:
            if shutil.which(bin_name):
                found_bin = bin_name
                break

        if not found_bin:
            # Check if name is any binary on PATH
            if shutil.which(name):
                found_bin = name
            else:
                found_bin = candidates[0]

        # Windows Execution Dispatcher
        if IS_WINDOWS:
            if found_bin in ("code.cmd", "code.exe", "code"):
                cmd = ["cmd.exe", "/c", "code"]
                if resolved_path:
                    cmd.append(str(resolved_path))
                if args:
                    cmd.extend(args)
                proc = subprocess.Popen(cmd, shell=True)
                return {
                    "success": True,
                    "app": "code",
                    "cmd": cmd,
                    "resolved_path": str(resolved_path) if resolved_path else None,
                    "pid": proc.pid
                }
            elif found_bin == "wt.exe":
                cmd = ["wt.exe"]
                if resolved_path:
                    cmd.extend(["-d", str(resolved_path)])
                if args:
                    cmd.extend(args)
                proc = subprocess.Popen(cmd)
                return {
                    "success": True,
                    "app": "wt.exe",
                    "cmd": cmd,
                    "resolved_path": str(resolved_path) if resolved_path else None,
                    "pid": proc.pid
                }
            elif found_bin == "cmd.exe":
                cmd = ["cmd.exe", "/K", f"cd /d {resolved_path}"] if resolved_path else ["cmd.exe"]
                proc = subprocess.Popen(cmd)
                return {
                    "success": True,
                    "app": "cmd.exe",
                    "cmd": cmd,
                    "resolved_path": str(resolved_path) if resolved_path else None,
                    "pid": proc.pid
                }
            elif found_bin == "powershell.exe":
                cmd = ["powershell.exe", "-NoExit", "-Command", f"Set-Location '{resolved_path}'"] if resolved_path else ["powershell.exe"]
                proc = subprocess.Popen(cmd)
                return {
                    "success": True,
                    "app": "powershell.exe",
                    "cmd": cmd,
                    "resolved_path": str(resolved_path) if resolved_path else None,
                    "pid": proc.pid
                }
            elif found_bin == "explorer.exe":
                target = str(resolved_path) if resolved_path else os.path.expanduser("~")
                proc = subprocess.Popen(["explorer.exe", target])
                return {
                    "success": True,
                    "app": "explorer.exe",
                    "resolved_path": target,
                    "pid": proc.pid
                }
            else:
                cmd = [found_bin]
                if resolved_path:
                    cmd.append(str(resolved_path))
                if args:
                    cmd.extend(args)
                proc = subprocess.Popen(cmd, shell=True)
                return {
                    "success": True,
                    "app": found_bin,
                    "cmd": cmd,
                    "resolved_path": str(resolved_path) if resolved_path else None,
                    "pid": proc.pid
                }

        # Linux Execution Dispatcher
        cmd = [found_bin]

        # Handle specific app requirements for directory/path
        if found_bin == "code":
            if resolved_path:
                cmd.append(str(resolved_path))
            if args:
                cmd.extend(args)
            proc = subprocess.Popen(cmd)
            return {
                "success": True,
                "app": found_bin,
                "cmd": cmd,
                "resolved_path": str(resolved_path) if resolved_path else None,
                "pid": proc.pid
            }

        elif found_bin in ("gnome-terminal", "x-terminal-emulator", "xfce4-terminal", "terminator"):
            if resolved_path:
                cmd.append(f"--working-directory={resolved_path}")
            if args:
                cmd.extend(args)
            proc = subprocess.Popen(cmd, cwd=str(resolved_path) if resolved_path and resolved_path.is_dir() else None)
            return {
                "success": True,
                "app": found_bin,
                "cmd": cmd,
                "resolved_path": str(resolved_path) if resolved_path else None,
                "pid": proc.pid
            }

        elif found_bin in ("nemo", "nautilus", "thunar", "dolphin", "pcmanfm"):
            target = str(resolved_path) if resolved_path else os.path.expanduser("~")
            cmd.append(target)
            if args:
                cmd.extend(args)
            proc = subprocess.Popen(cmd)
            return {
                "success": True,
                "app": found_bin,
                "cmd": cmd,
                "resolved_path": target,
                "pid": proc.pid
            }

        elif found_bin in ("google-chrome", "firefox", "chromium", "chromium-browser"):
            if resolved_path:
                cmd.append(str(resolved_path))
            elif args:
                cmd.extend(args)
            try:
                proc = subprocess.Popen(cmd)
                return {
                    "success": True,
                    "app": found_bin,
                    "cmd": cmd,
                    "resolved_path": str(resolved_path) if resolved_path else None,
                    "pid": proc.pid
                }
            except Exception:
                import webbrowser
                target_url = str(resolved_path) if resolved_path else "https://www.google.com"
                webbrowser.open(target_url)
                return {
                    "success": True,
                    "app": "browser_fallback",
                    "url": target_url
                }

        elif found_bin == "xdg-open":
            target = str(resolved_path) if resolved_path else os.path.expanduser("~")
            proc = subprocess.Popen(["xdg-open", target])
            return {
                "success": True,
                "app": "xdg-open",
                "resolved_path": target,
                "pid": proc.pid
            }

        else:
            # Generic application execution
            if resolved_path:
                cmd.append(str(resolved_path))
            if args:
                cmd.extend(args)
            cwd_target = str(resolved_path) if resolved_path and resolved_path.is_dir() else None
            try:
                proc = subprocess.Popen(cmd, cwd=cwd_target)
                return {
                    "success": True,
                    "app": found_bin,
                    "cmd": cmd,
                    "resolved_path": str(resolved_path) if resolved_path else None,
                    "pid": proc.pid
                }
            except Exception as e:
                try:
                    proc = subprocess.Popen(["gtk-launch", name])
                    return {"success": True, "app": name, "via": "gtk-launch"}
                except Exception:
                    pass
                raise OSAutomationException(f"Failed to launch application '{name}': {e}", violation_code="APP_LAUNCH_FAILED")

    async def search_web(self, query: str):
        """Opens web browser with Google Search."""
        import webbrowser
        encoded = urllib.parse.quote(query)
        webbrowser.open(f"https://www.google.com/search?q={encoded}")

    async def open_url(self, url: str):
        """Opens specified URL in web browser."""
        import webbrowser
        if not url.startswith("http://") and not url.startswith("https://"):
            url = f"https://{url}"
        webbrowser.open(url)

    async def set_volume(self, action: str):
        """Adjusts system audio volume (up, down, mute, unmute)."""
        act = action.lower()
        if IS_WINDOWS:
            if "up" in act or "+" in act or "besarkan" in act or "tambah" in act:
                subprocess.run(["powershell", "-Command", "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"], capture_output=True)
            elif "down" in act or "-" in act or "kecilkan" in act or "kurang" in act:
                subprocess.run(["powershell", "-Command", "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"], capture_output=True)
            elif "mute" in act or "senyap" in act or "matikan" in act:
                subprocess.run(["powershell", "-Command", "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"], capture_output=True)
        else:
            if "up" in act or "+" in act or "besarkan" in act or "tambah" in act:
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+10%"])
            elif "down" in act or "-" in act or "kecilkan" in act or "kurang" in act:
                subprocess.run(["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-10%"])
            elif "mute" in act or "senyap" in act or "matikan" in act:
                subprocess.run(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"])

    async def take_screenshot(self) -> Optional[Path]:
        """Captures whole desktop screen and saves to snapshots dir."""
        try:
            save_path = self.snapshots_dir / f"screenshot_{int(time.time())}.png"
            img = pyautogui.screenshot()
            img.save(str(save_path))
            return save_path
        except Exception as e:
            print(f"[OSController] Screenshot error: {e}")
            return None

    async def capture_webcam_snapshot(self) -> Optional[Path]:
        """Captures single frame from default webcam using OpenCV."""
        try:
            cap = cv2.VideoCapture(0)
            if not cap.isOpened():
                return None
            ret, frame = cap.read()
            cap.release()
            if not ret or frame is None:
                return None

            filename = f"webcam_{int(time.time())}.jpg"
            save_path = self.snapshots_dir / filename
            cv2.imwrite(str(save_path), frame)
            return save_path
        except Exception as e:
            print(f"[OSController] Webcam capture error: {e}")
            return None

    async def write_file(self, filepath: str, content: str) -> Path:
        """Writes content to local file with path security validation."""
        path_obj = Path(filepath).expanduser().resolve()
        is_bad, code, matched = OSProtectionGuardrail.check_command(str(path_obj))
        if is_bad:
            raise OSAutomationException(f"Write to protected path forbidden: {matched}", violation_code=code)

        path_obj.parent.mkdir(parents=True, exist_ok=True)
        path_obj.write_text(content, encoding="utf-8")
        return path_obj

    async def create_dir(self, dirpath: str) -> Path:
        """Creates directory with path security validation."""
        path_obj = Path(dirpath).expanduser().resolve()
        is_bad, code, matched = OSProtectionGuardrail.check_command(str(path_obj))
        if is_bad:
            raise OSAutomationException(f"Create dir at protected path forbidden: {matched}", violation_code=code)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj

    async def read_file(self, filepath: str, max_chars: int = 4000) -> str:
        """Reads content from local file with path security validation."""
        path_obj = Path(filepath).expanduser().resolve()
        is_bad, code, matched = OSProtectionGuardrail.check_command(str(path_obj))
        if is_bad:
            raise OSAutomationException(f"Read from protected path forbidden: {matched}", violation_code=code)
        if not path_obj.exists():
            raise FileNotFoundError(f"File '{filepath}' does not exist.")
        content = path_obj.read_text(encoding="utf-8", errors="replace")
        if len(content) > max_chars:
            return content[:max_chars] + f"\n... [Truncated remaining {len(content) - max_chars} characters]"
        return content

    def get_screen_size(self) -> Tuple[int, int]:
        return pyautogui.size()

    def get_cursor_pos(self) -> Tuple[int, int]:
        return pyautogui.position()
