#!/usr/bin/env python3
import sys
import os
from pathlib import Path

# Add backend directory to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from memory.db_manager import DatabaseManager

db = DatabaseManager()

def print_menu():
    cfg = db.get_active_llm_config()
    print("\n" + "=" * 62)
    print("           J.A.R.V.I.S. CONFIGURATION & AI SETUP")
    print("=" * 62)
    print(f" Current Provider : {cfg.get('provider_name', 'N/A')}")
    print(f" Current Model    : {cfg.get('model_name', 'N/A')}")
    api_key_masked = cfg.get('api_key', '')
    if len(api_key_masked) > 8:
        api_key_masked = api_key_masked[:4] + "..." + api_key_masked[-4:]
    print(f" Current API Key  : {api_key_masked}")
    print(f" Current Base URL : {cfg.get('base_url', 'Default')}")
    print("-" * 62)
    print(" [1] Change AI Provider")
    print(" [2] Change Model Name")
    print(" [3] Change API Key")
    print(" [4] Change Base URL")
    print(" [5] Quick Preset: Custom Endpoint (e.g. 9router / localhost)")
    print(" [6] Quick Preset: OpenAI Official")
    print(" [7] Quick Preset: OpenRouter")
    print(" [8] Quick Preset: Ollama (Local LLM)")
    print(" [0] Save & Exit")
    print("=" * 62)

def main():
    while True:
        cfg = db.get_active_llm_config()
        print_menu()
        try:
            choice = input("Select an option [0-8]: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nExiting configuration.")
            break

        if choice == "0":
            print("\nConfiguration saved successfully. Enjoy J.A.R.V.I.S.!")
            break
        elif choice == "1":
            print("\nAvailable providers: custom endpoint, openai, claude, openrouter, ollama")
            new_prov = input(f"Enter provider [{cfg.get('provider_name')}]: ").strip()
            if new_prov:
                db.save_llm_config(new_prov, cfg.get("model_name"), cfg.get("api_key"), cfg.get("base_url"))
                print(f"[OK] Provider updated to: {new_prov}")
        elif choice == "2":
            new_model = input(f"Enter model name [{cfg.get('model_name')}]: ").strip()
            if new_model:
                db.save_llm_config(cfg.get("provider_name"), new_model, cfg.get("api_key"), cfg.get("base_url"))
                print(f"[OK] Model name updated to: {new_model}")
        elif choice == "3":
            new_key = input("Enter new API Key: ").strip()
            if new_key:
                db.save_llm_config(cfg.get("provider_name"), cfg.get("model_name"), new_key, cfg.get("base_url"))
                print("[OK] API Key updated.")
        elif choice == "4":
            new_url = input(f"Enter Base URL [{cfg.get('base_url', '')}]: ").strip()
            db.save_llm_config(cfg.get("provider_name"), cfg.get("model_name"), cfg.get("api_key"), new_url or None)
            print(f"[OK] Base URL updated to: {new_url or 'Default'}")
        elif choice == "5":
            url = input("Enter Custom Endpoint Base URL [http://localhost:20128/v1]: ").strip() or "http://localhost:20128/v1"
            model = input("Enter model name [FreeTrial]: ").strip() or "FreeTrial"
            key = input("Enter API key (or press enter for default): ").strip() or cfg.get("api_key", "sk-default")
            db.save_llm_config("custom endpoint", model, key, url)
            print("[OK] Custom endpoint preset applied!")
        elif choice == "6":
            key = input("Enter OpenAI API Key: ").strip()
            model = input("Enter model [gpt-4o]: ").strip() or "gpt-4o"
            db.save_llm_config("openai", model, key, "https://api.openai.com/v1")
            print("[OK] OpenAI preset applied!")
        elif choice == "7":
            key = input("Enter OpenRouter API Key: ").strip()
            model = input("Enter model [anthropic/claude-3.5-sonnet]: ").strip() or "anthropic/claude-3.5-sonnet"
            db.save_llm_config("openrouter", model, key, "https://openrouter.ai/api/v1")
            print("[OK] OpenRouter preset applied!")
        elif choice == "8":
            url = input("Enter Ollama URL [http://localhost:11434/v1]: ").strip() or "http://localhost:11434/v1"
            model = input("Enter Ollama model [llama3]: ").strip() or "llama3"
            db.save_llm_config("custom endpoint", model, "ollama", url)
            print("[OK] Ollama preset applied!")
        else:
            print("[!] Invalid option. Please enter 0-8.")

if __name__ == "__main__":
    main()
