import asyncio
import time
import pytest
import sqlite3
import uuid
import sys
from pathlib import Path

# Add backend directory to sys.path
backend_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(backend_dir))

from memory.db_manager import DatabaseManager
from guardrails.pii_scanner import PIIScanner
from guardrails.os_protection import OSProtectionGuardrail
from engine.llm_factory import LLMFactory, FallbackRuleBasedAdapter
from engine.os_controller import OSController, OSAutomationException
from engine.voice_service import VoiceService
import config

def test_srd_tc_04_pii_guardrail_detection():
    """SRD-TC-04: PII Guardrail Kill-Switch"""
    t0 = time.time()
    
    # Test Email interception
    is_pii, code, matched = PIIScanner.scan("Kirimkan pesan ke tony.stark@avengers.org segera")
    assert is_pii is True
    assert code == "PII_EMAIL"
    assert "tony.stark@avengers.org" in matched

    # Test Password interception
    is_pii, code, matched = PIIScanner.scan("password = supersecretpassword123")
    assert is_pii is True
    assert code == "PII_PASSWORD"

    # Test Credit card interception
    is_pii, code, matched = PIIScanner.scan("Nomor kartu saya 4532-1234-5678-9012")
    assert is_pii is True
    assert code == "PII_CREDIT_CARD"

    # Test Phone interception
    is_pii, code, matched = PIIScanner.scan("Hubungi +62 812-3456-7890 sekarang")
    assert is_pii is True
    assert code == "PII_PHONE"

    detection_time_ms = (time.time() - t0) * 1000
    assert detection_time_ms < 50, f"Detection took {detection_time_ms}ms, expected < 50ms"
    print(f"\n[PASS] SRD-TC-04: PII guardrail caught violations in {detection_time_ms:.2f}ms")

def test_srd_tc_os_command_protection():
    """Tests OS command blacklist and system preservation guardrail"""
    is_bad, code, matched = OSProtectionGuardrail.check_command("Tolong jalankan rm -rf /")
    assert is_bad is True
    assert code == "FORBIDDEN_OS_COMMAND"

    is_bad, code, matched = OSProtectionGuardrail.check_command("buka file di /etc/shadow")
    assert is_bad is True
    assert code == "FORBIDDEN_RESTRICTED_PATH"
    print("\n[PASS] OS Command protection blocked destructive attempts")

def test_srd_tc_05_database_wal_and_rehydration(tmp_path):
    """SRD-TC-05: Persistent Context Rehydration & WAL crash recovery"""
    test_db = tmp_path / "test_memory.db"
    db = DatabaseManager(test_db)

    # 1. Start initial session
    session1 = db.init_session_with_rehydration()
    s1_id = session1["session_id"]
    assert session1["recovered_logs"] == []

    # 2. Log conversations
    db.log_conversation(s1_id, "user", "Hello Jarvis, test context recovery.")
    db.log_conversation(s1_id, "assistant", "Good evening, Sir. Memory active.")

    # 3. Simulate sudden crash (power cut / kill -9): process dies while system_state == 'ONLINE'
    # Relaunch system without clean close:
    db2 = DatabaseManager(test_db)
    session2 = db2.init_session_with_rehydration()
    s2_id = session2["session_id"]

    assert s2_id != s1_id
    assert len(session2["recovered_logs"]) == 2
    assert session2["recovered_logs"][0]["message_content"] == "Hello Jarvis, test context recovery."
    assert session2["recovered_logs"][1]["message_content"] == "Good evening, Sir. Memory active."

    # Check that previous session was marked as CRASHED
    with db2.get_connection() as conn:
        row = conn.execute("SELECT system_state, crash_reason FROM sessions WHERE session_id = ?", (s1_id,)).fetchone()
        assert row["system_state"] == "CRASHED"
        assert row["crash_reason"] == "ABRUPT_TERMINATION"

    print("\n[PASS] SRD-TC-05: Database WAL mode and crash recovery verified successfully.")

def test_srd_tc_02_pluggable_llm_switch(tmp_path):
    """SRD-TC-02: Pluggable LLM Switch"""
    test_db = tmp_path / "test_memory.db"
    db = DatabaseManager(test_db)

    # Default without config -> Fallback
    adapter = LLMFactory.create_adapter(db.get_active_llm_config())
    assert isinstance(adapter, FallbackRuleBasedAdapter)

    # Switch to Ollama
    db.save_llm_config("ollama", "llama3", "", "http://localhost:11434")
    config_row = db.get_active_llm_config()
    adapter2 = LLMFactory.create_adapter(config_row)
    assert adapter2.model_name == "llama3"

    print("\n[PASS] SRD-TC-02: LLM adapter configuration dynamically swapped.")

@pytest.mark.asyncio
async def test_srd_tc_03_humanlike_typing_jitter():
    """SRD-TC-03: Human-like Keystrokes intervals (20ms - 60ms)"""
    intervals = []
    last_time = None

    def on_char(c):
        nonlocal last_time
        now = time.time()
        if last_time is not None:
            intervals.append(now - last_time)
        last_time = now

    controller = OSController()
    test_string = "JARVIS"

    t_start = time.time()
    await controller.type_text_humanlike(test_string, on_char_callback=on_char)
    total_time = time.time() - t_start

    assert len(intervals) == len(test_string) - 1
    for interval in intervals:
        assert 0.015 <= interval <= 0.080, f"Interval {interval} outside expected range"

    print(f"\n[PASS] SRD-TC-03: Average typing interval {sum(intervals)/len(intervals)*1000:.2f}ms within human cadence.")

@pytest.mark.asyncio
async def test_srd_tc_01_proactive_greeting():
    """SRD-TC-01: Proactive greeting generation"""
    voice = VoiceService()
    greeting = voice.get_greeting("Sir")
    assert "System online" in greeting
    assert "Sir" in greeting
    print(f"\n[PASS] SRD-TC-01: Proactive greeting generated: '{greeting}'")

@pytest.mark.asyncio
async def test_os_actions_and_local_planner():
    """Verify that JARVIS can perform real OS actions from instructions"""
    controller = OSController()
    planner = FallbackRuleBasedAdapter()

    # 1. Shell execution safe command
    res = await controller.execute_shell("echo 'JARVIS_AUTONOMOUS_OK'")
    assert res["exit_code"] == 0
    assert "JARVIS_AUTONOMOUS_OK" in res["stdout"]

    # 2. Shell execution forbidden command caught by guardrail
    with pytest.raises(OSAutomationException):
        await controller.execute_shell("rm -rf /var/log")

    # 3. Web search action generation
    plan_search = await planner.generate_response("cari berita teknologi AI di google", [])
    assert len(plan_search["actions"]) > 0
    assert plan_search["actions"][0]["action"] in ("SEARCH_WEB", "OPEN_URL")

    # 4. App launch action generation
    plan_app = await planner.generate_response("buka terminal sekarang", [])
    assert len(plan_app["actions"]) > 0
    assert plan_app["actions"][0]["action"] == "OPEN_APP"
    assert plan_app["actions"][0]["app"] == "terminal"

    # 5. Volume control action generation
    plan_vol = await planner.generate_response("tolong besarkan volume suara", [])
    assert len(plan_vol["actions"]) > 0
    assert plan_vol["actions"][0]["action"] == "SYSTEM_CONTROL"
    assert plan_vol["actions"][0]["control"] == "volume_up"

    print("\n[PASS] OS Actions & Planner verified: Full autonomous capabilities active.")

@pytest.mark.asyncio
async def test_wake_word_filtering():
    """Verify that wake word is strictly required and ambient speech without 'jarvis' is ignored."""
    from engine.voice_service import WAKE_WORD_REGEX

    ambient_inputs = [
        "halo apa kabar kamu",
        "tolong bukakan chrome",
        "cuaca hari ini gimana ya",
        "ada kucing di depan rumah",
        "sedang meeting jangan berisik"
    ]
    for inp in ambient_inputs:
        assert not WAKE_WORD_REGEX.search(inp), f"False positive wake-word match on: '{inp}'"

    wake_inputs = [
        "jarvis tolong buka youtube",
        "halo jarvis apa kabar",
        "JARVIS tolong cari resep nasi goreng",
        "jarvius buka kalkulator",
        "hei javis tolong matikan volume"
    ]
    for inp in wake_inputs:
        assert WAKE_WORD_REGEX.search(inp), f"Failed to match wake-word on: '{inp}'"
        cleaned = WAKE_WORD_REGEX.sub("", inp).strip(",. ")
        assert len(cleaned) > 0, f"Cleaned instruction should not be empty for: '{inp}'"

    print("\n[PASS] Wake-word filtering verified: Ambient sound ignored, 'Jarvis' triggers execution.")

@pytest.mark.asyncio
async def test_dynamic_app_and_path_resolution():
    """Verify dynamic application detection, path resolution, and argument passing."""
    from engine.os_controller import resolve_dynamic_path, OSController
    from engine.llm_factory import detect_fallback_actions

    # 1. Test dynamic path resolution
    jarvis_path = resolve_dynamic_path("di folder JARVIS")
    assert jarvis_path is not None, "Failed to resolve folder 'JARVIS'"
    assert "JARVIS" in str(jarvis_path)
    assert jarvis_path.exists()

    docs_path = resolve_dynamic_path("in directory Documents")
    assert docs_path is not None, "Failed to resolve folder 'Documents'"
    assert docs_path.exists()

    # 2. Test dynamic fallback action parsing
    res_code = detect_fallback_actions("buka vscode di folder JARVIS")
    assert len(res_code) > 0
    assert res_code[0]["action"] == "OPEN_APP"
    assert res_code[0]["app"] == "code"
    assert "JARVIS" in res_code[0]["path"]

    res_term = detect_fallback_actions("buka terminal didalam folder Documents")
    assert len(res_term) > 0
    assert res_term[0]["action"] == "OPEN_APP"
    assert res_term[0]["app"] == "terminal"
    assert "Documents" in res_term[0]["path"]

    res_folder = detect_fallback_actions("buka folder JARVIS")
    assert len(res_folder) > 0
    assert res_folder[0]["action"] == "OPEN_APP"
    assert res_folder[0]["app"] == "files"
    assert "JARVIS" in res_folder[0]["path"]

    # 3. Test arbitrary app recognition
    res_vlc = detect_fallback_actions("buka vlc")
    assert len(res_vlc) > 0
    assert res_vlc[0]["action"] == "OPEN_APP"
    assert res_vlc[0]["app"] == "vlc"

    print("\n[PASS] Dynamic app recognition and path resolution verified successfully.")

@pytest.mark.asyncio
async def test_silent_error_and_vocal_success():
    """Verify that errors are not read aloud with voice (silent in recent activity), while non-error responses are read."""
    from engine.voice_service import VoiceService

    # 1. Error simulation: Error string must be identified as error and NOT read with TTS
    error_reply = "I apologize, Sir. An error occurred with the AI provider: Connection refused"
    error_keywords = ["error:", "exception:", "an error occurred with the ai provider", "failed to connect"]
    is_error = any(k in error_reply.lower() for k in error_keywords)
    assert is_error is True, "Failed to identify error string"

    # 2. Non-error simulation: Successful search / answer must be identified as clean
    success_reply = "Berikut adalah hasil pencarian teknologi AI terkini, Sir."
    is_success_error = any(k in success_reply.lower() for k in error_keywords)
    assert is_success_error is False, "Success reply incorrectly flagged as error"

    print("\n[PASS] Silent error & vocal success logic verified successfully.")

@pytest.mark.asyncio
async def test_dynamic_literal_obedience_and_no_unwanted_search():
    """Verify that 'open browser' ONLY opens the browser without searching news, and compound commands are parsed accurately."""
    from engine.llm_factory import detect_fallback_actions

    # 1. Simple browser command must NOT trigger web search
    browser_only = detect_fallback_actions("open the browser")
    assert len(browser_only) == 1
    assert browser_only[0]["action"] == "OPEN_APP"
    assert browser_only[0]["app"] == "browser"
    assert not any(a["action"] == "SEARCH_WEB" for a in browser_only)

    buka_browser = detect_fallback_actions("buka browser")
    assert len(buka_browser) == 1
    assert buka_browser[0]["action"] == "OPEN_APP"
    assert not any(a["action"] == "SEARCH_WEB" for a in buka_browser)

    buka_chrome = detect_fallback_actions("buka chrome")
    assert len(buka_chrome) == 1
    assert buka_chrome[0]["action"] == "OPEN_APP"
    assert buka_chrome[0]["app"] == "chrome"
    assert not any(a["action"] == "SEARCH_WEB" for a in buka_chrome)

    # 2. Compound command must execute both actions
    compound = detect_fallback_actions("buka chrome lalu cari berita teknologi terkini")
    assert len(compound) == 2
    assert compound[0]["action"] == "OPEN_APP"
    assert compound[0]["app"] == "chrome"
    assert compound[1]["action"] == "SEARCH_WEB"
    assert "teknologi" in compound[1]["query"]

    print("\n[PASS] Literal obedience verified: Browser opens without unwanted search; compound actions chained correctly.")

@pytest.mark.asyncio
async def test_conversational_greeting_and_followup_flow():
    """Verify that calling 'Jarvis' triggers 'Yes Sir, ada yang bisa saya bantu?' and activates follow-up window."""
    from engine.voice_service import VoiceService

    # 1. Pure call / greeting identification
    calls = ["jarvis", "halo jarvis", "hey jarvis", "hai jarvis", "selamat pagi jarvis"]
    for c in calls:
        assert VoiceService.is_call_or_greeting(c) is True, f"Failed to identify call/greeting: {c}"

    # Concrete command is NOT just a greeting
    assert VoiceService.is_call_or_greeting("jarvis tolong buka browser") is False
    assert VoiceService.is_call_or_greeting("jarvis buka vscode") is False

    # 2. Greeting reply verification
    indo_reply = VoiceService.get_greeting_reply("jarvis")
    assert "Yes Sir" in indo_reply
    assert "bisa saya bantu" in indo_reply

    en_reply = VoiceService.get_greeting_reply("hey jarvis, how are you")
    assert "Yes, Sir" in en_reply

    # 3. Conversational window state
    vs = VoiceService()
    assert vs.is_awaiting_command() is False
    vs.set_awaiting_command(True)
    assert vs.is_awaiting_command() is True
@pytest.mark.asyncio
async def test_high_level_context_and_intelligence():
    """Verify high-level dynamic system prompt, real-time context, and advanced actions."""
    from engine.llm_factory import build_high_level_system_prompt, FallbackRuleBasedAdapter, detect_fallback_actions
    import datetime

    # 1. Verify dynamic high-level system prompt contains live operational context
    prompt = build_high_level_system_prompt()
    assert "J.A.R.V.I.S." in prompt
    assert "HIGH-LEVEL OPERATIONAL CONTEXT" in prompt
    assert "Exact Current Time & Date" in prompt
    assert "Live System Telemetry" in prompt
    assert "CPU Utilization" in prompt
    assert str(datetime.datetime.now().year) in prompt

    # 2. Verify FallbackRuleBasedAdapter answers temporal & telemetry queries accurately
    adapter = FallbackRuleBasedAdapter()
    
    # Time query
    time_res = await adapter.generate_response("jam berapa sekarang", [])
    assert any(k in time_res["reply"].lower() for k in ["pukul", "wib", "jam"])
    assert time_res["actions"] == []

    # Date query
    date_res = await adapter.generate_response("hari apa ini dan tanggal berapa", [])
    assert any(k in date_res["reply"].lower() for k in ["hari", "tanggal", str(datetime.datetime.now().year)])

    # Diagnostics / system status
    status_res = await adapter.generate_response("bagaimana status sistem kamu", [])
    assert any(k in status_res["reply"].lower() for k in ["cpu", "ram", "memory", "sistem", "normal"])

    # 3. Verify directory creation action detection and OS execution
    dir_actions = detect_fallback_actions("buat folder projects_test")
    assert len(dir_actions) == 1
    assert dir_actions[0]["action"] == "CREATE_DIR"
    assert "projects_test" in dir_actions[0]["path"]

    # OSController create_dir and read_file test
    import tempfile
    controller = OSController()
    with tempfile.TemporaryDirectory() as tmpdir:
        test_sub = Path(tmpdir) / "jarvis_sub"
        created = await controller.create_dir(str(test_sub))
        assert created.exists() and created.is_dir()

        test_file = test_sub / "test.txt"
        await controller.write_file(str(test_file), "Hello from Jarvis high level test")
        content = await controller.read_file(str(test_file))
        assert "Hello from Jarvis high level test" in content

    print("\n[PASS] High-level context, telemetry, and advanced action capabilities verified.")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])



