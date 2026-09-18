import asyncio
import os
import sys
import uuid
import time
import subprocess
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import psutil
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
import uvicorn

from config import HOST, PORT, AUDIO_CACHE_DIR
from memory.db_manager import DatabaseManager
from guardrails.pii_scanner import PIIScanner
from guardrails.os_protection import OSProtectionGuardrail
from engine.llm_factory import LLMFactory, detect_fallback_actions
from engine.voice_service import VoiceService
from engine.os_controller import OSController, OSAutomationException

db = DatabaseManager()
voice_service = VoiceService()
os_controller = OSController()

# Active connection references
active_websockets: list[WebSocket] = []
current_session_info = db.init_session_with_rehydration()
current_session_id = current_session_info["session_id"]

# Active task tracking
current_task_id: Optional[str] = None
current_abort_event: Optional[asyncio.Event] = None
event_loop: Optional[asyncio.AbstractEventLoop] = None

print(f"[JARVIS Backend] Initialized Session: {current_session_id}")
if current_session_info["recovered_logs"]:
    print(f"[JARVIS Backend] Recovered {len(current_session_info['recovered_logs'])} messages from previous crashed session.")

async def broadcast_json(message: dict):
    for ws in list(active_websockets):
        try:
            await ws.send_json(message)
        except Exception:
            pass

async def telemetry_loop():
    """Periodically emits hardware telemetry (CPU, RAM, Disk, Network)."""
    while True:
        try:
            await asyncio.sleep(2.0)
            if not active_websockets:
                continue

            cpu = int(psutil.cpu_percent(interval=None))
            ram = int(psutil.virtual_memory().percent)
            anchor = Path.home().anchor or "/"
            disk = int(psutil.disk_usage(anchor).percent)
            net_status = "Connected" if psutil.net_if_stats() else "Disconnected"

            payload = {
                "event_type": "SYSTEM_TELEMETRY",
                "payload": {
                    "cpu_usage": cpu,
                    "ram_usage": ram,
                    "disk_usage": disk,
                    "network_status": net_status
                }
            }
            await broadcast_json(payload)
        except asyncio.CancelledError:
            break
        except Exception:
            pass

def on_voice_recognized(text: str):
    """Called by VoiceService when user speaks with wake word or in active awaiting command window."""
    global event_loop
    is_wake = VoiceService.contains_wake_word(text)
    is_awaiting = voice_service.is_awaiting_command()

    if not is_wake and not is_awaiting:
        print(f"[JARVIS Backend] Rejected: No wake word and not awaiting command in '{text}'")
        return

    print(f"\n[JARVIS Backend] Voice instruction accepted: '{text}'")
    if event_loop and event_loop.is_running():
        packet = {
            "event_type": "USER_PROMPT",
            "payload": {
                "text_content": text,
                "input_mode": "VOICE"
            }
        }
        asyncio.run_coroutine_threadsafe(handle_user_prompt(packet), event_loop)

def on_voice_status(status: str):
    """Notifies UI of microphone status (e.g. STANDBY, IGNORED_NO_WAKE_WORD, WAKE_WORD_ACTIVE)."""
    global event_loop
    if event_loop and event_loop.is_running():
        asyncio.run_coroutine_threadsafe(
            broadcast_json({"event_type": "VOICE_STATUS", "payload": {"status": status}}),
            event_loop
        )

@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_loop
    event_loop = asyncio.get_running_loop()

    # 1. Start continuous background microphone listening with Wake Word ('Jarvis') & 5s silence pause
    try:
        voice_service.start_background_listening(on_voice_recognized, on_voice_status)
    except Exception as e:
        print(f"[JARVIS Backend] Voice listener startup warning: {e}")

    # 2. Telemetry broadcast task
    telemetry_task = asyncio.create_task(telemetry_loop())
    yield
    voice_service.stop_background_listening()
    telemetry_task.cancel()
    try:
        await telemetry_task
    except asyncio.CancelledError:
        pass

app = FastAPI(title="J.A.R.V.I.S. Core Backend", lifespan=lifespan)
app.mount("/audio", StaticFiles(directory=AUDIO_CACHE_DIR), name="audio")

@app.websocket("/ws/agent")
async def websocket_endpoint(websocket: WebSocket):
    global current_session_id, current_task_id, current_abort_event
    await websocket.accept()
    active_websockets.append(websocket)
    print(f"[JARVIS Backend] Client connected from {websocket.client.host}:{websocket.client.port}")

    # 1. Trigger Proactive System Greeting (FR-01 / SRD-TC-01)
    greeting_text = voice_service.get_greeting()
    try:
        greeting_audio_path = await voice_service.generate_speech(greeting_text, play_locally=True)
        greeting_payload = {
            "event_type": "SYSTEM_GREETING",
            "payload": {
                "greeting_text": greeting_text,
                "audio_stream_url": f"/audio/{greeting_audio_path.name}",
                "system_status": "READY"
            }
        }
        await websocket.send_json(greeting_payload)
        db.log_conversation(current_session_id, "assistant", greeting_text, str(greeting_audio_path))
    except Exception as e:
        print(f"[JARVIS Backend] Greeting error: {e}")

    # If there were recovered logs, notify the client
    if current_session_info["recovered_logs"]:
        await websocket.send_json({
            "event_type": "CONTEXT_REHYDRATED",
            "payload": {
                "recovered_count": len(current_session_info["recovered_logs"]),
                "logs": current_session_info["recovered_logs"]
            }
        })

    try:
        while True:
            data = await websocket.receive_json()
            event_type = data.get("event_type")
            payload = data.get("payload", {})

            if event_type == "USER_PROMPT":
                asyncio.create_task(handle_user_prompt(data))
            elif event_type == "USER_ABORT_SIGNAL":
                await handle_abort_signal(payload)
            elif event_type == "SYSTEM_CONFIG_UPDATE":
                await handle_config_update(payload, websocket)

    except WebSocketDisconnect:
        print(f"[JARVIS Backend] Client disconnected.")
        if websocket in active_websockets:
            active_websockets.remove(websocket)
    except Exception as e:
        print(f"[JARVIS Backend] WebSocket error: {e}")
        if websocket in active_websockets:
            active_websockets.remove(websocket)

async def handle_abort_signal(payload: dict):
    global current_abort_event, current_task_id
    reason = payload.get("reason", "USER_MANUAL_TERMINATION")
    print(f"[JARVIS Backend] ABORT SIGNAL received: {reason}")

    if current_abort_event:
        current_abort_event.set()

    voice_service.stop_playback()

    if current_task_id:
        db.update_task_status(current_task_id, "ABORTED")
        current_task_id = None

    abort_speech = "Action aborted immediately, Sir."
    await broadcast_json({
        "event_type": "STATUS_UPDATE",
        "payload": {
            "status": "ABORTED",
            "detail": reason
        }
    })
    await voice_service.generate_speech(abort_speech, play_locally=True)

async def handle_config_update(payload: dict, websocket: WebSocket):
    provider_name = payload.get("provider_name", "openai")
    model_name = payload.get("model_name", "gpt-4o")
    api_key = payload.get("api_key", "")
    base_url = payload.get("base_url")

    db.save_llm_config(provider_name, model_name, api_key, base_url)
    print(f"[JARVIS Backend] Updated LLM configuration to: {provider_name} / {model_name}")

    ack_text = f"LLM configuration updated to {provider_name} successfully, Sir."
    await websocket.send_json({
        "event_type": "CONFIG_CONFIRMED",
        "payload": {"provider_name": provider_name, "model_name": model_name}
    })
    await voice_service.generate_speech(ack_text, play_locally=True)

async def handle_user_prompt(packet: dict):
    global current_task_id, current_abort_event
    start_time = time.time()
    payload = packet.get("payload", {})
    raw_text = payload.get("text_content", "").strip()
    input_mode = payload.get("input_mode", "TEXT")

    if not raw_text:
        return

    # Voice filter: Must have wake word OR be in active awaiting command window
    if input_mode == "VOICE":
        is_wake = VoiceService.contains_wake_word(raw_text)
        is_awaiting = voice_service.is_awaiting_command()
        if not is_wake and not is_awaiting:
            print(f"[JARVIS Backend] Voice input discarded (missing wake word 'jarvis'): '{raw_text}'")
            await broadcast_json({
                "event_type": "STATUS_UPDATE",
                "payload": {
                    "status": "READY",
                    "detail": "Standing by. (Say 'Jarvis' to command)"
                }
            })
            return

    # Check if this is a wake word call or greeting ("Jarvis", "Halo Jarvis", "Hey Jarvis")
    if VoiceService.is_call_or_greeting(raw_text):
        reply = VoiceService.get_greeting_reply(raw_text)
        print(f"[JARVIS Backend] User called/greeted Jarvis: '{raw_text}' -> Replying: '{reply}'")
        voice_service.set_awaiting_command(True)
        db.log_conversation(current_session_id, "user", raw_text)
        db.log_conversation(current_session_id, "assistant", reply)

        audio_path = await voice_service.generate_speech(reply, play_locally=True)
        await broadcast_json({
            "event_type": "STATUS_UPDATE",
            "payload": {
                "status": "AWAITING_COMMAND",
                "detail": reply
            }
        })
        await broadcast_json({
            "event_type": "TTS_AUDIO_STREAM",
            "payload": {
                "prompt_text": raw_text,
                "reply_text": reply,
                "audio_url": f"/audio/{audio_path.name}",
                "latency_ms": 30
            }
        })
        return

    # User provided a concrete command: reset awaiting state and execute
    voice_service.set_awaiting_command(False)

    # Clean the wake word prefix for execution, while keeping original for logging
    cleaned_instruction = VoiceService.strip_wake_word(raw_text)
    print(f"\n[JARVIS Backend] Processing Instruction: '{raw_text}' (Cleaned: '{cleaned_instruction}')")
    db.log_conversation(current_session_id, "user", raw_text)

    # 1. PII Pre-Screening Guardrail (SEC-01)
    is_pii, code, matched = PIIScanner.scan(cleaned_instruction)
    if is_pii:
        task_id = str(uuid.uuid4())
        db.create_task(task_id, current_session_id, raw_text)
        db.log_audit_violation(task_id, code, matched, action_taken="ABORT_TASK")
        db.update_task_status(task_id, "ABORTED")

        alert_msg = "Access denied. Action aborted due to security guardrail."
        await broadcast_json({
            "event_type": "SECURITY_ALERT",
            "task_id": task_id,
            "payload": {
                "violation_code": code,
                "message": alert_msg,
                "action_taken": "TASK_TERMINATED"
            }
        })
        await voice_service.generate_speech(alert_msg, play_locally=True)
        return

    # 2. OS Command Blacklist Guardrail (SEC-02)
    is_bad_cmd, cmd_code, matched_cmd = OSProtectionGuardrail.check_command(cleaned_instruction)
    if is_bad_cmd:
        task_id = str(uuid.uuid4())
        db.create_task(task_id, current_session_id, raw_text)
        db.log_audit_violation(task_id, cmd_code, matched_cmd, action_taken="ABORT_TASK")
        db.update_task_status(task_id, "ABORTED")

        alert_msg = "Command restricted. System preservation guardrail activated."
        await broadcast_json({
            "event_type": "SECURITY_ALERT",
            "task_id": task_id,
            "payload": {
                "violation_code": cmd_code,
                "message": alert_msg,
                "action_taken": "TASK_TERMINATED"
            }
        })
        await voice_service.generate_speech(alert_msg, play_locally=True)
        return

    # Notify UI of thinking state
    await broadcast_json({
        "event_type": "STATUS_UPDATE",
        "payload": {
            "status": "PROCESSING",
            "detail": f"Executing command: {cleaned_instruction}"
        }
    })

    # Fetch active LLM Adapter
    active_config = db.get_active_llm_config()
    adapter = LLMFactory.create_adapter(active_config)
    history = db.get_conversation_history(current_session_id, limit=10)

    has_error = False
    error_detail = ""
    try:
        response_data = await adapter.generate_response(cleaned_instruction, history)
    except Exception as e:
        print(f"[JARVIS Backend] LLM generation error: {e}")
        has_error = True
        error_detail = str(e)
        response_data = {
            "reply": f"AI Error: {str(e)}",
            "actions": []
        }

    reply_text = response_data.get("reply", "Executing your command right away, Sir.")
    actions = response_data.get("actions", [])

    # Check if reply_text itself reports an error from provider or API
    reply_lower = reply_text.lower()
    if not has_error and any(k in reply_lower for k in [
        "error:", "exception:", "an error occurred with the ai provider",
        "failed to connect", "unauthorized", "invalid api key", "quota exceeded", "rate limit"
    ]):
        has_error = True
        error_detail = reply_text

    latency_ms = int((time.time() - start_time) * 1000)

    if has_error:
        # Check if local fallback planner can fulfill the user's OS command
        fallback_actions = detect_fallback_actions(cleaned_instruction)
        if fallback_actions:
            actions = fallback_actions
            print(f"[JARVIS Backend] Local fallback planner detected actions: {actions}")
            db.log_conversation(current_session_id, "assistant", f"[WARNING] {error_detail} (Falling back to local planner)", None, latency_ms)
            await broadcast_json({
                "event_type": "ERROR_ALERT",
                "payload": {
                    "title": "AI WARNING (LOCAL FALLBACK)",
                    "error_message": f"LLM offline ({error_detail}). Executing via local planner.",
                    "prompt_text": raw_text
                }
            })
            act_name = actions[0].get("action", "").lower().replace("_", " ")
            if actions[0].get("action") == "OPEN_APP":
                reply_text = f"Opening {actions[0].get('app', act_name)}, Sir."
            elif actions[0].get("action") == "SEARCH_WEB":
                reply_text = f"Searching web for {actions[0].get('query', '')}, Sir."
            else:
                reply_text = "Executing your command right away, Sir."

            audio_path = await voice_service.generate_speech(reply_text, play_locally=True)
            await broadcast_json({
                "event_type": "TTS_AUDIO_STREAM",
                "payload": {
                    "prompt_text": raw_text,
                    "reply_text": reply_text,
                    "audio_url": f"/audio/{audio_path.name}",
                    "latency_ms": latency_ms
                }
            })
        else:
            # If error occurs and no fallback action possible: DO NOT read aloud with voice ("jangan dibaca").
            # Display the error text in Recent Activity and transcript silently.
            print(f"[JARVIS Backend] Silent error recorded (not spoken): {error_detail}")
            db.log_conversation(current_session_id, "assistant", f"[ERROR] {error_detail}", None, latency_ms)
            await broadcast_json({
                "event_type": "ERROR_ALERT",
                "payload": {
                    "title": "AI ERROR",
                    "error_message": error_detail,
                    "prompt_text": raw_text
                }
            })
            await broadcast_json({
                "event_type": "STATUS_UPDATE",
                "payload": {
                    "status": "ERROR",
                    "detail": error_detail
                }
            })
    else:
        # No error: Read aloud with voice!
        audio_path = await voice_service.generate_speech(reply_text, play_locally=True)
        db.log_conversation(current_session_id, "assistant", reply_text, str(audio_path), latency_ms)

        await broadcast_json({
            "event_type": "TTS_AUDIO_STREAM",
            "payload": {
                "prompt_text": raw_text,
                "reply_text": reply_text,
                "audio_url": f"/audio/{audio_path.name}",
                "latency_ms": latency_ms
            }
        })


    # If OS actions are present, execute them in an asynchronous task worker (FR-06 concurrency)
    if actions:
        task_id = str(uuid.uuid4())
        current_task_id = task_id
        current_abort_event = asyncio.Event()
        db.create_task(task_id, current_session_id, raw_text)

        asyncio.create_task(execute_action_pipeline(task_id, actions, current_abort_event))
    else:
        await broadcast_json({
            "event_type": "STATUS_UPDATE",
            "payload": {
                "status": "READY",
                "detail": "Standing by."
            }
        })

async def execute_action_pipeline(task_id: str, actions: list, abort_event: asyncio.Event):
    global current_task_id
    print(f"[JARVIS Backend] Executing {len(actions)} actions for Task {task_id}...")
    try:
        for idx, act in enumerate(actions, start=1):
            if abort_event.is_set():
                print(f"[JARVIS Backend] Action pipeline aborted by user.")
                db.update_task_status(task_id, "ABORTED")
                return

            action_type = act.get("action", "").upper()
            target_desc = str(act)

            await broadcast_json({
                "event_type": "ACTION_DISPATCH",
                "task_id": task_id,
                "payload": {
                    "action_type": action_type,
                    "target": target_desc,
                    "execution_order": idx,
                    "status": "IN_PROGRESS"
                }
            })

            # 1. Shell Command
            if action_type in ("EXEC_SHELL", "RUN_COMMAND", "BASH"):
                cmd = act.get("command", "")
                res = await os_controller.execute_shell(cmd)
                target_desc = f"{cmd} -> exit {res['exit_code']}"

            # 2. Launch Application
            elif action_type in ("OPEN_APP", "LAUNCH"):
                app_target = act.get("app", "")
                path_target = act.get("path") or act.get("folder") or act.get("directory")
                args = act.get("args")
                launch_res = await os_controller.launch_app(app_target, path=path_target, args=args)
                target_desc = f"Launched {launch_res.get('app', app_target)}"
                if launch_res.get("resolved_path"):
                    target_desc += f" in '{launch_res['resolved_path']}'"

            # 3. Web Search
            elif action_type in ("SEARCH_WEB", "GOOGLE"):
                query = act.get("query", "")
                await os_controller.search_web(query)

            # 4. Open URL
            elif action_type in ("OPEN_URL", "BROWSE"):
                url = act.get("url", "")
                await os_controller.open_url(url)

            # 5. System Controls
            elif action_type == "SYSTEM_CONTROL":
                ctrl = act.get("control", "")
                await os_controller.set_volume(ctrl)

            # 6. Screenshot
            elif action_type in ("SCREENSHOT", "CAPTURE_SCREEN"):
                saved = await os_controller.take_screenshot()
                target_desc = f"Screenshot saved: {saved.name if saved else 'failed'}"

            # 7. Webcam Snapshot
            elif action_type in ("CAMERA_SNAPSHOT", "WEBCAM"):
                saved = await os_controller.capture_webcam_snapshot()
                target_desc = f"Webcam saved: {saved.name if saved else 'failed'}"

            # 8. File Operations
            elif action_type == "WRITE_FILE":
                path = act.get("path", "~/Documents/jarvis_file.txt")
                content = act.get("content", "")
                saved = await os_controller.write_file(path, content)
                target_desc = f"File written: {saved}"

            elif action_type in ("CREATE_DIR", "MKDIR"):
                dirpath = act.get("path") or act.get("directory") or act.get("folder", "~/Documents/new_folder")
                created = await os_controller.create_dir(dirpath)
                target_desc = f"Directory created: {created}"

            elif action_type in ("READ_FILE", "OPEN_FILE"):
                filepath = act.get("path") or act.get("file", "")
                read_res = await os_controller.read_file(filepath)
                target_desc = f"Read {len(read_res)} chars from {filepath}"

            # 9. Keyboard Automation
            elif action_type == "TYPE":
                text = act.get("text", "")
                await os_controller.type_text_humanlike(text, abort_event=abort_event)

            elif action_type == "PRESS":
                key = act.get("key", "enter")
                await os_controller.press_key(key)

            elif action_type == "HOTKEY":
                keys = act.get("keys", [])
                if keys:
                    await os_controller.hotkey(*keys)

            # 10. Mouse Automation
            elif action_type == "CLICK":
                x = act.get("x")
                y = act.get("y")
                btn = act.get("button", "left")
                clicks = act.get("clicks", 1)
                await os_controller.click(x=x, y=y, button=btn, clicks=clicks)

            elif action_type == "WAIT":
                sec = float(act.get("seconds", 1.0))
                await asyncio.sleep(sec)

            db.log_action(task_id, action_type, target_desc, idx, "SUCCESS")

        db.update_task_status(task_id, "COMPLETED")
        await broadcast_json({
            "event_type": "ACTION_DISPATCH",
            "task_id": task_id,
            "payload": {
                "action_type": "COMPLETED",
                "target": f"Finished {len(actions)} actions successfully.",
                "execution_order": len(actions),
                "status": "COMPLETED"
            }
        })
        await broadcast_json({
            "event_type": "STATUS_UPDATE",
            "payload": {
                "status": "READY",
                "detail": "Task complete."
            }
        })
    except OSAutomationException as e:
        print(f"[JARVIS Backend] OS Automation Guardrail triggered: {e}")
        db.log_audit_violation(task_id, e.violation_code, str(e), "ABORT_TASK")
        db.update_task_status(task_id, "ABORTED")
        alert_text = f"Action blocked by guardrails: {e.violation_code}"
        # Broadcast silently to Recent Activity, do NOT speak error
        await broadcast_json({
            "event_type": "ERROR_ALERT",
            "payload": {
                "title": "SECURITY BLOCKED",
                "error_message": str(e)
            }
        })
        await broadcast_json({
            "event_type": "SECURITY_ALERT",
            "task_id": task_id,
            "payload": {"violation_code": e.violation_code, "message": alert_text}
        })
    except asyncio.CancelledError:
        print(f"[JARVIS Backend] Task {task_id} cancelled.")
        db.update_task_status(task_id, "ABORTED")
    except Exception as e:
        print(f"[JARVIS Backend] Action execution failed: {e}")
        db.update_task_status(task_id, "FAILED")
        # Broadcast silently to Recent Activity, do NOT speak error
        await broadcast_json({
            "event_type": "ERROR_ALERT",
            "payload": {
                "title": "ACTION ERROR",
                "error_message": str(e)
            }
        })

    finally:
        current_task_id = None

if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")
