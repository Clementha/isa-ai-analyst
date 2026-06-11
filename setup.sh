# Copyright (c) 2026 Clement Ha
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

#!/bin/bash

# Ensure the .env file exists so we can check it safely
touch .env

# ANSI Color Codes for Greying out text
RESET="\033[0m"
GREY="\033[90m"

# Single Source of Truth for the default model
DEFAULT_LLM_MODEL="openrouter/anthropic/claude-haiku-4-5"

show_menu() {
    clear
    echo "================================================="
    echo "🤖 ISA AI ANALYST - SETUP"
    echo "================================================="
    
    # 1. Check Docker Status
    AGENT_RUNNING=false
    if [ "$(docker ps -q -f name=isa_ai_analyst)" ]; then
        AGENT_RUNNING=true
        echo "Status: 🟢 RUNNING"
    else
        echo "Status: 🔴 STOPPED / NOT INSTALLED"
    fi
    echo "-------------------------------------------------"
    
    # 2. Dynamic Checkboxes (Reads the .env file)
    LLM_CHECK="[ ]"
    T212_CHECK="[ ]"
    EOD_CHECK="[ ]"
    TG_CHECK="[ ]"
    SETUP_CHECK="[ ]"
    
    ALL_KEYS_SET=true
    if grep -q "^LLM_API_KEY=." .env; then LLM_CHECK="[✓]"; else ALL_KEYS_SET=false; fi
    if grep -q "^T212_KEY_ID=." .env && grep -q "^T212_SECRET=." .env; then T212_CHECK="[✓]"; else ALL_KEYS_SET=false; fi
    if grep -q "^EODHD_API_KEY=." .env; then EOD_CHECK="[✓]"; else ALL_KEYS_SET=false; fi
    if grep -q "^TELEGRAM_BOT_TOKEN=." .env && grep -q "^TELEGRAM_CHAT_ID=." .env; then TG_CHECK="[✓]"; else ALL_KEYS_SET=false; fi

    # Setup is only "Done" if the file exists AND all keys are set
    SETUP_DONE=false
    if [ -f "openclaw_data/openclaw.json" ] && [ "$ALL_KEYS_SET" = true ]; then
        SETUP_CHECK="[✓]"
        SETUP_DONE=true
    fi

    echo " SETUP CHECKLIST:"
    echo "  1) $LLM_CHECK 🧠 Set AI API Key (OpenRouter)"
    echo "  2) $T212_CHECK ❤️ Set Broker API Keys (Trading 212)"
    echo "  3) $EOD_CHECK 👁️  Set Market Data API Key (EODHD)"
    echo "  4) $TG_CHECK 👄 Set Telegram API Keys"
    
    # Grey out Initial Setup if keys aren't done
    if [ "$ALL_KEYS_SET" = true ]; then
        echo "  5) $SETUP_CHECK 🛠️  Run Initial Setup"
    else
        echo -e "${GREY}  5) $SETUP_CHECK 🛠️  Run Initial Setup (Complete keys first)${RESET}"
    fi

    echo "-------------------------------------------------"
    echo " CONTROLS:"
    
    # Grey out Start/Stop/Logs if setup isn't done (1-5 checked)
    if [ "$SETUP_DONE" = true ]; then
        echo "  6) 🚀 Start Agent"
        echo "  7) 🛑 Stop Agent"
        echo "  8) 📋 View Live Logs"
    else
        echo -e "${GREY}  6) 🚀 Start Agent (Run Setup first)${RESET}"
        echo -e "${GREY}  7) 🛑 Stop Agent (Run Setup first)${RESET}"
        echo -e "${GREY}  8) 📋 View Live Logs (Run Setup first)${RESET}"
    fi
    
    # Grey out Telegram pairing if the agent isn't running
    if [ "$AGENT_RUNNING" = true ]; then
        echo "  9) 🔑 Approve Telegram Pairing"
    else
        echo -e "${GREY}  9) 🔑 Approve Telegram Pairing (Agent must be running)${RESET}"
    fi

    echo "  0) ❌ Exit"
    echo "================================================="
    read -p "Enter choice [0-9]: " choice
    
    case $choice in
        1) set_llm ;;
        2) set_t212 ;;
        3) set_eodhd ;;
        4) set_tg ;;
        5) 
            if [ "$ALL_KEYS_SET" = true ]; then run_setup
            else echo -e "\n⚠️  Please complete steps 1-4 first!" && sleep 2; fi 
            ;;
        6) 
            if [ "$SETUP_DONE" = true ]; then start_bot
            else echo -e "\n⚠️  Please complete Steps 1-5 first!" && sleep 2; fi 
            ;;
        7) 
            if [ "$SETUP_DONE" = true ]; then stop_bot
            else echo -e "\n⚠️  Please complete Steps 1-5 first!" && sleep 2; fi 
            ;;
        8) 
            if [ "$SETUP_DONE" = true ]; then view_logs
            else echo -e "\n⚠️  Please complete Steps 1-5 first!" && sleep 2; fi 
            ;;
        9) 
            if [ "$AGENT_RUNNING" = true ]; then pair_telegram
            else echo -e "\n⚠️  The Agent must be running to approve pairing!" && sleep 2; fi 
            ;;
        0) exit 0 ;;
        *) echo "Invalid option." && sleep 2 ;;
    esac
}

# --- KEY SETTERS ---
set_key() {
    # Removes old key if exists, writes new key
    grep -v "^$1=" .env > .env.tmp && mv .env.tmp .env
    echo "$1=$2" >> .env
}

set_llm() {
    echo ""
    read -p "Paste your OpenRouter API Key (or press Enter to cancel): " key
    if [ -z "$key" ]; then echo "⚠️  No input detected. Cancelled."; sleep 1.5; return; fi
    
    set_key "LLM_API_KEY" "$key"
    set_key "OPENROUTER_API_KEY" "$key"
    set_key "LLM_MODEL" "$DEFAULT_LLM_MODEL"
    set_key "LLM_BASE_URL" "https://openrouter.ai/api/v1/chat/completions" 
    echo "✅ AI API Key Saved!" && sleep 1
}

set_t212() {
    echo ""
    read -p "Paste your Trading 212 Key ID (or press Enter to cancel): " t212_id
    if [ -z "$t212_id" ]; then echo "⚠️  No input detected. Cancelled."; sleep 1.5; return; fi
    
    read -p "Paste your Trading 212 Secret Key (or press Enter to cancel): " t212_sec
    if [ -z "$t212_sec" ]; then echo "⚠️  No input detected. Cancelled."; sleep 1.5; return; fi
    
    set_key "T212_KEY_ID" "$t212_id"
    set_key "T212_SECRET" "$t212_sec"
    echo "✅ Broker API Keys Saved!" && sleep 1
}

set_eodhd() {
    echo ""
    read -p "Paste your EODHD API Key (or press Enter to cancel): " eodhd
    if [ -z "$eodhd" ]; then echo "⚠️  No input detected. Cancelled."; sleep 1.5; return; fi
    
    set_key "EODHD_API_KEY" "$eodhd"
    echo "✅ Market API Key Saved!" && sleep 1
}

set_tg() {
    echo ""
    read -p "Paste your Telegram Bot Token (or press Enter to cancel): " token
    if [ -z "$token" ]; then echo "⚠️  No input detected. Cancelled."; sleep 1.5; return; fi
    
    read -p "Paste your Telegram Chat ID (or press Enter to cancel): " chatid
    if [ -z "$chatid" ]; then echo "⚠️  No input detected. Cancelled."; sleep 1.5; return; fi
    
    set_key "TELEGRAM_BOT_TOKEN" "$token"
    set_key "TELEGRAM_CHAT_ID" "$chatid"
    echo "✅ Telegram API Keys Saved!" && sleep 1
}

# --- DOCKER CONTROLS ---
run_setup() {
    echo -e "\n🐳 Booting Docker Container to build dependencies..."
    source .env
    
    echo "🧠 Pre-loading AI Agent Brain (Workspace files)..."
    # CREATE WORKSPACE AND COPY FILES BEFORE DOCKER BOOTS
    mkdir -p openclaw_data/workspace
    cp config/*.md openclaw_data/workspace/ 2>/dev/null || true
    
    # 1. Boot up naturally
    docker compose up -d > /dev/null 2>&1
    
    echo -e "\n⏳ Installing dependencies & booting agent... (This takes about 30-60 seconds)"
    echo -e "${GREY}Please wait, do not close the terminal...${RESET}"
    
    while true; do
        if docker logs isa_ai_analyst 2>&1 | grep -q "starting provider"; then
            break
        fi
        sleep 2
    done
    
    echo "🧠 Configuring AI Model via Official CLI..."
    # 2. THE NATIVE FIX: We let OpenClaw's own CLI safely write the model to openclaw.json
    docker exec isa_ai_analyst openclaw config set agents.defaults.model.primary "$DEFAULT_LLM_MODEL" > /dev/null 2>&1
    # Keep Telegram answer-streaming but hide transient tool-execution/progress chatter
    docker exec isa_ai_analyst openclaw config set channels.telegram.streaming.preview.toolProgress false > /dev/null 2>&1

    echo "💉 Safely injecting API Keys..."
    # 3. Auth profiles are perfectly fine to manually inject
    mkdir -p openclaw_data/agents/main/agent
    cat <<EOF > openclaw_data/agents/main/agent/auth-profiles.json
{
  "meta": { "lastTouchedVersion": "2026.3.28" },
  "openrouter": { "apiKey": "$LLM_API_KEY" }
}
EOF
    
    echo "🔄 Reloading Agent to apply keys..."
    docker compose restart > /dev/null 2>&1
    
    echo -e "\n✅ Setup Complete! The Agent is fully configured and running."
    read -p "Press Enter to return to menu..."
}

start_bot() {
    echo -e "\n🚀 Starting Agent..."
    docker compose start
    sleep 2
}

stop_bot() {
    echo -e "\n🛑 Stopping Agent..."
    docker compose stop
    sleep 2
}

view_logs() {
    echo -e "\n📋 Tailing logs... (Press Ctrl+C to return to menu)"
    docker logs -f isa_invest_claw
}

pair_telegram() {
    echo ""
    read -p "Enter the pairing code sent to your Telegram (or press Enter to cancel): " pairing_code
    if [ -z "$pairing_code" ]; then echo "⚠️  Cancelled."; sleep 1.5; return; fi
    
    echo "🔗 Sending pairingapproval to Telegram..."
    docker exec -it isa_ai_analyst openclaw pairing approve telegram "$pairing_code"
    read -p "Press Enter to return to menu..."
}

# Start the infinite menu loop
while true; do
    show_menu
done