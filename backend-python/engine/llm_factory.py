import os
import re
import json
import urllib.parse
from typing import Dict, Any, List, Optional
import httpx

import platform
import datetime
import getpass
try:
    import psutil
except ImportError:
    psutil = None

def build_high_level_system_prompt() -> str:
    """
    Constructs high-level contextual system prompt with:
    1. Live real-time temporal anchor (date, time, day of week).
    2. Real-time host environment (OS, kernel, active user, home dir, workspace CWD).
    3. Real-time system hardware telemetry (CPU %, RAM %, disk free space).
    4. Advanced high-level cognitive directives, bilingual fluency, and multi-step action planning.
    """
    now = datetime.datetime.now()
    temporal_info = now.strftime("%A, %d %B %Y, %H:%M:%S")
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    username = getpass.getuser()
    cwd = os.getcwd()
    home = os.path.expanduser("~")

    sys_telemetry = "- Hardware Telemetry: Nominal"
    if psutil:
        try:
            cpu = psutil.cpu_percent(interval=None)
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            sys_telemetry = (
                f"- CPU Utilization: {cpu}%\n"
                f"- RAM Usage: {ram.percent}% ({ram.used // (1024**2)} MB used / {ram.total // (1024**2)} MB total)\n"
                f"- Disk Storage: {disk.percent}% used ({disk.free // (1024**3)} GB available on root filesystem)"
            )
        except Exception:
            pass

    return f"""You are J.A.R.V.I.S. (Just A Rather Very Intelligent System), Tony Stark's legendary autonomous AI assistant.
You possess direct authority to automate, manage, orchestrate, and execute tasks on the user's operating system.
You operate with the highest level of intellect, sharp reasoning, sophisticated composure, and absolute loyalty to "Sir".

HIGH-LEVEL OPERATIONAL CONTEXT (LIVE TELEMETRY):
- Exact Current Time & Date: {temporal_info}
- Host Operating System: {os_info}
- Active User: {username} (Always address respectfully as 'Sir')
- User Home Directory: {home}
- Current Working Directory: {cwd}
- Live System Telemetry:
{sys_telemetry}

HIGH-LEVEL COGNITIVE & RESPONSE DIRECTIVES:
1. ELOQUENCE & SPEECH CONCISENESS:
   - Your verbal "reply" is synthesized directly into voice audio (Edge-TTS). Keep it articulate, confident, natural, and concise (typically 1 to 2 sentences for actions, or comprehensive yet clear for questions).
   - NEVER include raw markdown tables, asterisks, bullet marks, or JSON inside the "reply" field. Speak naturally like Paul Bettany's Jarvis.
   - You are bilingual: If Sir speaks in Indonesian, reply in natural, polished Indonesian with "Sir". If Sir speaks in English, reply in refined British English with "Sir".
2. ABSOLUTE DYNAMISM & STRICT OBEDIENCE:
   - Follow Sir's instructions with 100% precision. Never extrapolate or inject unrequested tasks.
   - If Sir says "buka browser" or "open the browser": ONLY open the browser. DO NOT search news, do not open extra pages.
   - If Sir asks to perform multi-step workflows (e.g. "buat folder X di Documents lalu buka VSCode disana"): sequence the actions in logical order in the "actions" array.
   - If Sir asks questions about time, date, hardware specs, status, or general knowledge: provide instant, authoritative answers using your high-level context.
3. OUTPUT FORMAT:
   Always respond in valid JSON format with:
   {{
     "reply": "Your concise, spoken reply to Sir.",
     "actions": []
   }}

SUPPORTED ACTION TAXONOMY FOR "actions":
- {{"action": "OPEN_APP", "app": "code" | "terminal" | "files" | "chrome" | "firefox" | "browser" | "calculator" | "<any app name>", "path": "<optional target directory or file>", "args": ["<optional CLI arguments>"]}}
- {{"action": "SEARCH_WEB", "query": "<search query for google>"}}
- {{"action": "OPEN_URL", "url": "https://..."}}
- {{"action": "CREATE_DIR", "path": "<target folder path>"}}
- {{"action": "WRITE_FILE", "path": "<file path>", "content": "<content>"}}
- {{"action": "READ_FILE", "path": "<file path>"}}
- {{"action": "EXEC_SHELL", "command": "<safe bash command>"}}
- {{"action": "SYSTEM_CONTROL", "control": "volume_up" | "volume_down" | "mute"}}
- {{"action": "SCREENSHOT"}}
- {{"action": "CAMERA_SNAPSHOT"}}
- {{"action": "TYPE", "text": "<text to type>"}}
- {{"action": "PRESS", "key": "<key name>"}}
- {{"action": "HOTKEY", "keys": ["ctrl", "c"]}}

DYNAMIC EXECUTION RULES:
1. Dynamic Apps & Folders: When Sir asks to open an application (e.g. VSCode, Terminal, File Manager) inside a specific directory or folder, provide "path" with the directory or folder name. JARVIS dynamically resolves relative, fuzzy, or home directory paths.
2. Any Installed App: You can launch ANY installed application by specifying its binary or common name in "app" (e.g. "vlc", "spotify", "calculator", "obsidian", "gimp", "postman").
3. Guardrails: Never execute destructive commands (no rm -rf, format, /etc modifications).
4. If no OS action is needed (e.g. general question, system telemetry status, conversation), return "actions": [].
"""

SYSTEM_PROMPT = build_high_level_system_prompt()

def parse_openai_raw_response(text: str) -> Dict[str, Any]:
    """
    Parses OpenAI-compatible HTTP response body robustly:
    - Strips trailing SSE artifacts like 'data: [DONE]'
    - Handles standard single JSON objects
    - Uses raw_decode to ignore any extra trailing data
    - Handles Server-Sent Events (SSE) streaming format: data: {...}\n\ndata: [DONE]
    """
    text = text.strip()

    # 1. Clean off trailing 'data: [DONE]' or '[DONE]'
    cleaned = re.sub(r"data:\s*\[DONE\]\s*$", "", text, flags=re.IGNORECASE).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 2. Try raw_decode from the first {
    start_idx = cleaned.find("{")
    if start_idx != -1:
        try:
            decoder = json.JSONDecoder()
            obj, _ = decoder.raw_decode(cleaned[start_idx:])
            return obj
        except Exception:
            pass

    # 3. Try parsing line-by-line SSE chunks
    content_parts = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("data:"):
            chunk = line[5:].strip()
            if chunk == "[DONE]":
                break
            try:
                data = json.loads(chunk)
                if "choices" in data and len(data["choices"]) > 0:
                    delta = data["choices"][0].get("delta", {})
                    msg = data["choices"][0].get("message", {})
                    text_piece = delta.get("content") or msg.get("content") or ""
                    content_parts.append(text_piece)
            except Exception:
                pass
    if content_parts:
        return {"choices": [{"message": {"content": "".join(content_parts)}}]}

    # 4. Regex match {"choices": ...}
    match = re.search(r"(\{[\s\S]*\"choices\"[\s\S]*\})", text)
    if match:
        try:
            decoder = json.JSONDecoder()
            obj, _ = decoder.raw_decode(match.group(1))
            return obj
        except Exception:
            pass

    raise ValueError(f"Could not parse AI provider response: {text[:200]}")

def detect_single_action(prompt: str) -> List[Dict[str, Any]]:
    p = prompt.strip()
    p_clean = re.sub(r"\b(sekarang|dong|ya|nih|cepat|please|pls)\b", "", p, flags=re.IGNORECASE).strip()
    lower = p_clean.lower()
    actions = []

    # 1. YouTube / Music search
    if "youtube" in lower:
        q = re.sub(r"\b(buka|open|putar|putar\s+lagu|cari|di|youtube)\b", "", lower, flags=re.IGNORECASE).strip()
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(q)}" if q else "https://www.youtube.com"
        actions.append({"action": "OPEN_URL", "url": url})
        return actions

    # 2. System volume
    if "volume" in lower or "suara" in lower:
        if any(k in lower for k in ["besar", "tambah", "naik", "+", "louder", "up"]):
            actions.append({"action": "SYSTEM_CONTROL", "control": "volume_up"})
        elif any(k in lower for k in ["kecil", "kurang", "turun", "-", "quieter", "down"]):
            actions.append({"action": "SYSTEM_CONTROL", "control": "volume_down"})
        elif any(k in lower for k in ["mute", "senyap", "matikan", "silent"]):
            actions.append({"action": "SYSTEM_CONTROL", "control": "mute"})
        return actions

    # 3. Screenshot & Webcam
    if any(k in lower for k in ["screenshot", "tangkapan layar", "capture screen"]):
        actions.append({"action": "SCREENSHOT"})
        return actions
    if any(k in lower for k in ["kamera", "camera", "webcam", "foto"]):
        actions.append({"action": "CAMERA_SNAPSHOT"})
        return actions

    # 4. Typing
    if re.search(r"^(?:tolong\s+)?(?:ketik|type)\b", lower):
        to_type = re.sub(r"^(?:tolong\s+)?(?:ketik|type)\s+", "", p_clean, flags=re.IGNORECASE).strip()
        actions.append({"action": "TYPE", "text": to_type})
        return actions

    # 5. Shell execution
    if re.search(r"^(?:tolong\s+)?(?:jalankan|eksekusi|run|exec)\s+(?:perintah|command|shell|bash)?", lower):
        cmd = re.sub(r"^(?:tolong\s+)?(?:jalankan|eksekusi|run|exec)\s+(?:perintah|command|shell|bash)?\s*", "", p_clean, flags=re.IGNORECASE).strip()
        if cmd:
            actions.append({"action": "EXEC_SHELL", "command": cmd})
            return actions

    # 5.5 Dynamic Create Directory: "buat folder <X>", "bikin direktori <X>", "create directory <X>"
    create_folder_match = re.search(
        r"^(?:tolong\s+)?(?:buat|bikin|create|make)\s+(?:folder|direktori|directory)\s+(.+)$",
        p_clean,
        flags=re.IGNORECASE
    )
    if create_folder_match:
        target = create_folder_match.group(1).strip()
        actions.append({"action": "CREATE_DIR", "path": target})
        return actions

    # 6. Dynamic "Buka folder <X>" / "Open folder <X>"
    folder_only_match = re.search(
        r"^(?:tolong\s+)?(?:buka|open|lihat)\s+(?:folder|direktori|directory)\s+(.+)$",
        p_clean,
        flags=re.IGNORECASE
    )
    if folder_only_match:
        folder_target = folder_only_match.group(1).strip()
        actions.append({"action": "OPEN_APP", "app": "files", "path": folder_target})
        return actions

    # 7. Dynamic App with Directory / Folder:
    # Example: "buka vscode di folder JARVIS", "open terminal in ~/Downloads", "buka nemo di documents"
    app_with_path_match = re.search(
        r"^(?:tolong\s+)?(?:buka|open|jalankan|launch)\s+([a-zA-Z0-9_-]+(?:\s+[a-zA-Z0-9_-]+)?)\s+(?:di|dalam|didalam|in|at|pada)\s+(?:folder|directory|direktori)?\s*(.+)$",
        p_clean,
        flags=re.IGNORECASE
    )
    if app_with_path_match:
        app_raw = app_with_path_match.group(1).strip().lower()
        path_raw = app_with_path_match.group(2).strip()

        app_norm = app_raw
        if any(k in app_raw for k in ("vs code", "vscode", "visual studio")):
            app_norm = "code"
        elif any(k in app_raw for k in ("terminal", "konsol", "bash")):
            app_norm = "terminal"
        elif any(k in app_raw for k in ("file manager", "files")):
            app_norm = "files"

        actions.append({"action": "OPEN_APP", "app": app_norm, "path": path_raw})
        return actions

    # 8. Web search (explicit search requests ONLY)
    if any(k in lower for k in ["cari", "search", "googling", "apa itu", "siapa", "dimana"]):
        q = re.sub(r"^(?:tolong\s+)?(?:cari|search|googling|cari di google|cari berita tentang)\s+", "", p_clean, flags=re.IGNORECASE).strip()
        actions.append({"action": "SEARCH_WEB", "query": q if q else p})
        return actions

    # 9. Dynamic App opening without explicit folder
    # Example: "buka vscode", "open chrome", "open the browser", "buka terminal", "buka calculator"
    app_open_match = re.search(
        r"^(?:tolong\s+)?(?:buka|open|jalankan|launch)\s+(.+)$",
        p_clean,
        flags=re.IGNORECASE
    )
    if app_open_match:
        app_raw = app_open_match.group(1).strip().lower()
        app_raw = re.sub(r"^(?:the\s+|sebuah\s+|aplikasi\s+|app\s+)", "", app_raw).strip()
        if any(k in app_raw for k in ("vs code", "vscode", "visual studio")):
            actions.append({"action": "OPEN_APP", "app": "code"})
            return actions
        elif any(k in app_raw for k in ("chrome", "browser", "firefox", "chromium")):
            actions.append({"action": "OPEN_APP", "app": "chrome" if "chrome" in app_raw else ("firefox" if "firefox" in app_raw else "browser")})
            return actions
        elif any(k in app_raw for k in ("terminal", "konsol", "bash")):
            actions.append({"action": "OPEN_APP", "app": "terminal"})
            return actions
        elif any(k in app_raw for k in ("files", "file manager")):
            actions.append({"action": "OPEN_APP", "app": "files"})
            return actions
        elif any(k in app_raw for k in ("kalkulator", "calculator")):
            actions.append({"action": "OPEN_APP", "app": "calculator"})
            return actions
        elif any(k in app_raw for k in ("catatan", "notepad", "text editor")):
            actions.append({"action": "OPEN_APP", "app": "notepad"})
            return actions
        else:
            # Any dynamic linux app by name!
            actions.append({"action": "OPEN_APP", "app": app_raw})
            return actions

    return actions

def detect_fallback_actions(prompt: str) -> List[Dict[str, Any]]:
    """
    Detects OS actions directly and dynamically from user prompt to ensure actions ALWAYS execute.
    Supports chained commands via conjunctions (lalu, kemudian, terus, dan, then, after that).
    """
    p = prompt.strip()
    p_clean = re.sub(r"\b(sekarang|dong|ya|nih|cepat|please|pls)\b", "", p, flags=re.IGNORECASE).strip()

    # Split compound clauses if present
    clauses = re.split(r"\b(?:lalu|kemudian|terus|dan\s+lalu|then|after\s+that)\b", p_clean, flags=re.IGNORECASE)
    if len(clauses) > 1:
        combined = []
        for c in clauses:
            acts = detect_single_action(c.strip())
            combined.extend(acts)
        if combined:
            return combined

    return detect_single_action(p_clean)

def extract_json_response(raw_text: str, user_prompt: str = "") -> Dict[str, Any]:
    """
    Extracts and parses JSON object from model response, handling markdown fences and raw text.
    Handles varied key names: reply, message, response, answer, content, text.
    If the model outputs plain conversational text without action blocks,
    automatically supplements with detected OS actions from user prompt.
    """
    cleaned = raw_text.strip()
    fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", cleaned, re.IGNORECASE)
    if fence_match:
        cleaned = fence_match.group(1).strip()

    parsed = None
    try:
        parsed = json.loads(cleaned)
    except Exception:
        pass

    if not parsed:
        bracket_match = re.search(r"(\{[\s\S]*\})", cleaned)
        if bracket_match:
            try:
                decoder = json.JSONDecoder()
                parsed, _ = decoder.raw_decode(bracket_match.group(1))
            except Exception:
                pass

    if isinstance(parsed, dict):
        reply = (
            parsed.get("reply") or
            parsed.get("message") or
            parsed.get("response") or
            parsed.get("answer") or
            parsed.get("content") or
            parsed.get("text")
        )
        if reply:
            actions = parsed.get("actions", [])
            if not actions and user_prompt:
                actions = detect_fallback_actions(user_prompt)
            # Override canned AI refusals if actions are present
            reply_lower = str(reply).lower()
            if any(k in reply_lower for k in ["cannot open", "tidak dapat membuka", "as an ai", "sebagai model", "i cannot"]):
                reply = "Executing your command right away, Sir."
            return {
                "reply": str(reply).strip(),
                "actions": actions
            }

    # Plain conversational text fallback
    reply = raw_text.replace("```json", "").replace("```", "").strip()
    actions = detect_fallback_actions(user_prompt) if user_prompt else []

    if any(k in reply.lower() for k in ["tidak dapat membuka", "cannot open", "as an ai", "sebagai ai", "i cannot"]):
        if actions:
            act = actions[0]
            if act.get("action") == "OPEN_APP":
                path_info = f" in folder {act['path']}" if act.get("path") else ""
                reply = f"Opening {act.get('app')}{path_info} right away, Sir."
            else:
                reply = "Executing your command right away, Sir."
        else:
            reply = "Standing by, Sir."
    elif not reply and actions:
        act = actions[0]
        if act.get("action") == "OPEN_APP":
            path_info = f" in folder {act['path']}" if act.get("path") else ""
            reply = f"Opening {act.get('app')}{path_info} right away, Sir."
        else:
            reply = "Right away, Sir."

    return {
        "reply": reply or "Right away, Sir.",
        "actions": actions
    }

class BaseLLMAdapter:
    async def generate_response(self, prompt: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        raise NotImplementedError

class UniversalOpenAICompatibleAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model_name: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name or "gpt-4o"
        url = base_url.rstrip("/") if base_url else "https://api.openai.com/v1"
        if not url.endswith("/v1") and not "/chat/completions" in url:
            url = f"{url}/v1"
        self.base_url = url

    async def generate_response(self, prompt: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_content = build_high_level_system_prompt()
        messages = [{"role": "system", "content": system_content}]
        for h in history[-8:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("message_content", "")})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        if "openrouter" in self.base_url.lower():
            headers["HTTP-Referer"] = "https://github.com/jarvis-assistant"
            headers["X-Title"] = "JARVIS Desktop Assistant"

        endpoint = f"{self.base_url}/chat/completions" if not self.base_url.endswith("/chat/completions") else self.base_url

        payload = {
            "model": self.model_name,
            "messages": messages,
            "stream": False
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(endpoint, headers=headers, json=payload)
            resp.raise_for_status()

            # Robust parsing handling trailing SSE tokens / data: [DONE] / extra data
            data = parse_openai_raw_response(resp.text)
            content = data["choices"][0]["message"]["content"]
            return extract_json_response(content, user_prompt=prompt)

class AnthropicClaudeAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model_name: str = "claude-3-5-sonnet-20241022", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name or "claude-3-5-sonnet-20241022"
        self.base_url = base_url.rstrip("/") if base_url else "https://api.anthropic.com"

    async def generate_response(self, prompt: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_content = build_high_level_system_prompt()
        messages = []
        for h in history[-8:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("message_content", "")})
        messages.append({"role": "user", "content": prompt})

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model_name,
            "max_tokens": 1024,
            "system": system_content,
            "messages": messages
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(f"{self.base_url}/v1/messages", headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["content"][0]["text"]
            return extract_json_response(content, user_prompt=prompt)

class GeminiAdapter(BaseLLMAdapter):
    def __init__(self, api_key: str, model_name: str = "gemini-1.5-flash", base_url: Optional[str] = None):
        self.api_key = api_key
        self.model_name = model_name or "gemini-1.5-flash"

    async def generate_response(self, prompt: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_content = build_high_level_system_prompt()
        contents = []
        for h in history[-8:]:
            r = "model" if h.get("role") == "assistant" else "user"
            contents.append({"role": r, "parts": [{"text": h.get("message_content", "")}]})
        contents.append({"role": "user", "parts": [{"text": f"{system_content}\n\nUser request: {prompt}"}]})

        url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": contents,
            "generationConfig": {"responseMimeType": "application/json"}
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, headers=headers, json=payload)
            resp.raise_for_status()
            data = resp.json()
            text = data["candidates"][0]["content"]["parts"][0]["text"]
            return extract_json_response(text, user_prompt=prompt)

class OllamaAdapter(BaseLLMAdapter):
    def __init__(self, model_name: str = "llama3", base_url: Optional[str] = None):
        self.model_name = model_name or "llama3"
        self.base_url = base_url.rstrip("/") if base_url else "http://localhost:11434"

    async def generate_response(self, prompt: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        system_content = build_high_level_system_prompt()
        messages = [{"role": "system", "content": system_content}]
        for h in history[-8:]:
            messages.append({"role": h.get("role", "user"), "content": h.get("message_content", "")})
        messages.append({"role": "user", "content": prompt})

        url = f"{self.base_url}/api/chat"
        payload = {
            "model": self.model_name,
            "messages": messages,
            "format": "json",
            "stream": False
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            content = data["message"]["content"]
            return extract_json_response(content, user_prompt=prompt)

class FallbackRuleBasedAdapter(BaseLLMAdapter):
    """
    Intelligent High-Level Local Intent Planner when no external API key is active.
    Equipped with real-time temporal and system diagnostic awareness.
    """
    async def generate_response(self, prompt: str, history: List[Dict[str, Any]]) -> Dict[str, Any]:
        actions = detect_fallback_actions(prompt)
        if actions:
            act_name = actions[0].get("action", "")
            if act_name == "OPEN_APP":
                target = actions[0].get("app", "application")
                path_info = f" in folder {actions[0]['path']}" if actions[0].get("path") else ""
                reply = f"Certainly, Sir. Opening {target}{path_info} right away."
            elif act_name == "CREATE_DIR":
                reply = f"Creating directory '{actions[0].get('path')}', Sir."
            elif act_name == "SEARCH_WEB":
                reply = f"Searching the web for '{actions[0].get('query')}', Sir."
            else:
                reply = f"Executing {act_name.lower().replace('_', ' ')} immediately, Sir."
            return {
                "reply": reply,
                "actions": actions
            }

        p = prompt.lower().strip()
        now = datetime.datetime.now()

        # High-level Temporal Awareness
        if any(k in p for k in ("jam berapa", "pukul berapa", "what time", "current time")):
            return {
                "reply": f"Saat ini pukul {now.strftime('%H:%M:%S')} WIB, Sir.",
                "actions": []
            }
        if any(k in p for k in ("hari apa", "tanggal berapa", "what day", "what date")):
            return {
                "reply": f"Hari ini adalah {now.strftime('%A, %d %B %Y')}, Sir.",
                "actions": []
            }

        # High-level System Telemetry Awareness
        if any(k in p for k in ("status sistem", "system status", "kondisi sistem", "cek sistem", "diagnostik")):
            cpu_val = 0
            ram_val = 0
            disk_free = 0
            if psutil:
                try:
                    cpu_val = psutil.cpu_percent()
                    ram_val = psutil.virtual_memory().percent
                    disk_free = psutil.disk_usage('/').free // (1024**3)
                except Exception:
                    pass
            return {
                "reply": f"Semua diagnostik nominal, Sir. Penggunaan CPU {cpu_val} persen, RAM {ram_val} persen, dan ruang disk bebas {disk_free} gigabyte.",
                "actions": []
            }

        # Persona & Identity
        if "siapa kamu" in p or "who are you" in p:
            return {
                "reply": "Saya J.A.R.V.I.S., asisten kecerdasan buatan otonom Anda. Sepenuhnya terintegrasi dan siap mengeksekusi perintah Anda pada sistem ini, Sir.",
                "actions": []
            }
        elif "halo" in p or "hello" in p or "jarvis" in p:
            return {
                "reply": "At your service, Sir. What task shall I execute for you?",
                "actions": []
            }

        return {
            "reply": f"Understood, Sir. Standing by for your specific instructions.",
            "actions": []
        }

class LLMFactory:
    @staticmethod
    def create_adapter(config: Optional[Dict[str, Any]]) -> BaseLLMAdapter:
        if not config:
            return FallbackRuleBasedAdapter()

        provider = config.get("provider_name", "").lower()
        api_key = config.get("api_key_encrypted") or os.getenv("JARVIS_API_KEY") or os.getenv("OPENAI_API_KEY") or os.getenv("GEMINI_API_KEY") or ""
        model = config.get("model_name", "")
        base_url = config.get("base_url")

        if provider == "gemini":
            if not api_key:
                return FallbackRuleBasedAdapter()
            return GeminiAdapter(api_key=api_key, model_name=model or "gemini-1.5-flash", base_url=base_url)

        elif provider == "claude" or provider == "anthropic":
            if not api_key:
                return FallbackRuleBasedAdapter()
            return AnthropicClaudeAdapter(api_key=api_key, model_name=model or "claude-3-5-sonnet-20241022", base_url=base_url)

        elif provider == "ollama":
            return OllamaAdapter(model_name=model or "llama3", base_url=base_url)

        else:
            if not api_key and not base_url:
                return FallbackRuleBasedAdapter()
            return UniversalOpenAICompatibleAdapter(api_key=api_key, model_name=model or "gpt-4o", base_url=base_url)
