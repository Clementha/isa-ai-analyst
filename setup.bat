@echo off
setlocal EnableDelayedExpansion

:: Single Source of Truth for the default model
set DEFAULT_LLM_MODEL=openrouter/x-ai/grok-4.1-fast

:: Ensure .env exists
if not exist .env type nul > .env

:SHOW_MENU
cls
echo =================================================
echo  ISA AI ANALYST - SETUP
echo =================================================

:: Check Docker / agent status
set AGENT_RUNNING=false
for /f "delims=" %%i in ('docker ps -q -f name^=isa_ai_analyst 2^>nul') do (
    if not "%%i"=="" set AGENT_RUNNING=true
)

if "!AGENT_RUNNING!"=="true" (
    echo  Status: [RUNNING]
) else (
    echo  Status: [STOPPED / NOT INSTALLED]
)
echo -------------------------------------------------

:: Dynamic checkboxes — read .env
set LLM_CHECK=[ ]
set T212_CHECK=[ ]
set EOD_CHECK=[ ]
set TG_CHECK=[ ]
set SETUP_CHECK=[ ]
set ALL_KEYS_SET=true

findstr /r "^LLM_API_KEY=." .env >nul 2>&1
if errorlevel 1 ( set ALL_KEYS_SET=false ) else ( set LLM_CHECK=[OK] )

findstr /r "^T212_KEY_ID=." .env >nul 2>&1
if errorlevel 1 ( set ALL_KEYS_SET=false ) else (
    findstr /r "^T212_SECRET=." .env >nul 2>&1
    if errorlevel 1 ( set ALL_KEYS_SET=false ) else ( set T212_CHECK=[OK] )
)

findstr /r "^EODHD_API_KEY=." .env >nul 2>&1
if errorlevel 1 ( set ALL_KEYS_SET=false ) else ( set EOD_CHECK=[OK] )

findstr /r "^TELEGRAM_BOT_TOKEN=." .env >nul 2>&1
if errorlevel 1 ( set ALL_KEYS_SET=false ) else (
    findstr /r "^TELEGRAM_CHAT_ID=." .env >nul 2>&1
    if errorlevel 1 ( set ALL_KEYS_SET=false ) else ( set TG_CHECK=[OK] )
)

:: Setup is complete only if all keys set AND openclaw.json exists
set SETUP_DONE=false
if "!ALL_KEYS_SET!"=="true" (
    if exist openclaw_data\openclaw.json (
        set SETUP_CHECK=[OK]
        set SETUP_DONE=true
    )
)

echo  SETUP CHECKLIST:
echo   1) !LLM_CHECK!  Set AI API Key (OpenRouter)
echo   2) !T212_CHECK!  Set Broker API Keys (Trading 212)
echo   3) !EOD_CHECK!  Set Market Data API Key (EODHD)
echo   4) !TG_CHECK!  Set Telegram API Keys

if "!ALL_KEYS_SET!"=="true" (
    echo   5) !SETUP_CHECK!  Run Initial Setup
) else (
    echo   5) !SETUP_CHECK!  Run Initial Setup  ^(Complete keys first^)
)

echo -------------------------------------------------
echo  CONTROLS:

if "!SETUP_DONE!"=="true" (
    echo   6)  Start Agent
    echo   7)  Stop Agent
    echo   8)  View Live Logs
) else (
    echo   6)  Start Agent              ^(Run Setup first^)
    echo   7)  Stop Agent               ^(Run Setup first^)
    echo   8)  View Live Logs           ^(Run Setup first^)
)

if "!AGENT_RUNNING!"=="true" (
    echo   9)  Approve Telegram Pairing
) else (
    echo   9)  Approve Telegram Pairing  ^(Agent must be running^)
)

echo   0)  Exit
echo =================================================
set /p CHOICE="Enter choice [0-9]: "

if "!CHOICE!"=="1" goto SET_LLM
if "!CHOICE!"=="2" goto SET_T212
if "!CHOICE!"=="3" goto SET_EODHD
if "!CHOICE!"=="4" goto SET_TG
if "!CHOICE!"=="5" goto CHECK_SETUP
if "!CHOICE!"=="6" goto CHECK_START
if "!CHOICE!"=="7" goto CHECK_STOP
if "!CHOICE!"=="8" goto CHECK_LOGS
if "!CHOICE!"=="9" goto CHECK_PAIR
if "!CHOICE!"=="0" goto EXIT
echo Invalid option.
timeout /t 2 >nul
goto SHOW_MENU

:: -----------------------------------------------
:CHECK_SETUP
if "!ALL_KEYS_SET!"=="true" ( goto RUN_SETUP )
echo.
echo [!] Please complete steps 1-4 first!
timeout /t 2 >nul
goto SHOW_MENU

:CHECK_START
if "!SETUP_DONE!"=="true" ( goto START_BOT )
echo.
echo [!] Please complete Steps 1-5 first!
timeout /t 2 >nul
goto SHOW_MENU

:CHECK_STOP
if "!SETUP_DONE!"=="true" ( goto STOP_BOT )
echo.
echo [!] Please complete Steps 1-5 first!
timeout /t 2 >nul
goto SHOW_MENU

:CHECK_LOGS
if "!SETUP_DONE!"=="true" ( goto VIEW_LOGS )
echo.
echo [!] Please complete Steps 1-5 first!
timeout /t 2 >nul
goto SHOW_MENU

:CHECK_PAIR
if "!AGENT_RUNNING!"=="true" ( goto PAIR_TELEGRAM )
echo.
echo [!] The Agent must be running to approve pairing!
timeout /t 2 >nul
goto SHOW_MENU

:: -----------------------------------------------
:: KEY SETTERS
:: -----------------------------------------------

:SET_LLM
echo.
set /p LLM_KEY="Paste your OpenRouter API Key (or press Enter to cancel): "
if "!LLM_KEY!"=="" (
    echo [!] No input detected. Cancelled.
    timeout /t 2 >nul
    goto SHOW_MENU
)
call :WRITE_KEY LLM_API_KEY !LLM_KEY!
call :WRITE_KEY OPENROUTER_API_KEY !LLM_KEY!
call :WRITE_KEY LLM_MODEL %DEFAULT_LLM_MODEL%
call :WRITE_KEY LLM_BASE_URL https://openrouter.ai/api/v1/chat/completions
echo [OK] AI API Key Saved!
timeout /t 1 >nul
goto SHOW_MENU

:SET_T212
echo.
set /p T212_ID="Paste your Trading 212 Key ID (or press Enter to cancel): "
if "!T212_ID!"=="" (
    echo [!] No input detected. Cancelled.
    timeout /t 2 >nul
    goto SHOW_MENU
)
set /p T212_SEC="Paste your Trading 212 Secret Key (or press Enter to cancel): "
if "!T212_SEC!"=="" (
    echo [!] No input detected. Cancelled.
    timeout /t 2 >nul
    goto SHOW_MENU
)
call :WRITE_KEY T212_KEY_ID !T212_ID!
call :WRITE_KEY T212_SECRET !T212_SEC!
echo [OK] Broker API Keys Saved!
timeout /t 1 >nul
goto SHOW_MENU

:SET_EODHD
echo.
set /p EODHD_KEY="Paste your EODHD API Key (or press Enter to cancel): "
if "!EODHD_KEY!"=="" (
    echo [!] No input detected. Cancelled.
    timeout /t 2 >nul
    goto SHOW_MENU
)
call :WRITE_KEY EODHD_API_KEY !EODHD_KEY!
echo [OK] Market Data API Key Saved!
timeout /t 1 >nul
goto SHOW_MENU

:SET_TG
echo.
set /p TG_TOKEN="Paste your Telegram Bot Token (or press Enter to cancel): "
if "!TG_TOKEN!"=="" (
    echo [!] No input detected. Cancelled.
    timeout /t 2 >nul
    goto SHOW_MENU
)
set /p TG_CHATID="Paste your Telegram Chat ID (or press Enter to cancel): "
if "!TG_CHATID!"=="" (
    echo [!] No input detected. Cancelled.
    timeout /t 2 >nul
    goto SHOW_MENU
)
call :WRITE_KEY TELEGRAM_BOT_TOKEN !TG_TOKEN!
call :WRITE_KEY TELEGRAM_CHAT_ID !TG_CHATID!
echo [OK] Telegram API Keys Saved!
timeout /t 1 >nul
goto SHOW_MENU

:: -----------------------------------------------
:: DOCKER CONTROLS
:: -----------------------------------------------

:RUN_SETUP
echo.
echo [*] Pre-loading AI Agent Brain (Workspace files)...
if not exist openclaw_data\workspace mkdir openclaw_data\workspace
xcopy /s /y config\*.md openclaw_data\workspace\ >nul 2>&1

echo [*] Booting Docker Container...
docker compose up -d >nul 2>&1

echo [*] Waiting for agent to start... (This takes about 30-60 seconds)
echo     Please wait, do not close this window...

:WAIT_LOOP
timeout /t 2 >nul
docker logs isa_ai_analyst 2>&1 | findstr /c:"starting provider" >nul
if errorlevel 1 goto WAIT_LOOP

echo [*] Configuring AI Model via Official CLI...
for /f "tokens=*" %%v in ('type .env ^| findstr "^LLM_API_KEY="') do set LLM_VAL=%%v
set LLM_VAL=!LLM_VAL:LLM_API_KEY=!
docker exec isa_ai_analyst openclaw config set agents.defaults.model.primary "%DEFAULT_LLM_MODEL%" >nul 2>&1

echo [*] Safely injecting API Keys...
if not exist openclaw_data\agents\main\agent mkdir openclaw_data\agents\main\agent

:: Read LLM key from .env
for /f "tokens=1,* delims==" %%a in ('findstr "^LLM_API_KEY=" .env') do set INJECT_KEY=%%b

(
echo {
echo   "meta": { "lastTouchedVersion": "2026.3.28" },
echo   "openrouter": { "apiKey": "!INJECT_KEY!" }
echo }
) > openclaw_data\agents\main\agent\auth-profiles.json

echo [*] Reloading Agent to apply keys...
docker compose restart >nul 2>&1

echo.
echo [OK] Setup Complete! The Agent is fully configured and running.
pause
goto SHOW_MENU

:START_BOT
echo.
echo [*] Starting Agent...
docker compose start
timeout /t 2 >nul
goto SHOW_MENU

:STOP_BOT
echo.
echo [*] Stopping Agent...
docker compose stop
timeout /t 2 >nul
goto SHOW_MENU

:VIEW_LOGS
echo.
echo [*] Tailing logs... (Press Ctrl+C to stop)
docker logs -f isa_ai_analyst
goto SHOW_MENU

:PAIR_TELEGRAM
echo.
set /p PAIR_CODE="Enter the pairing code sent to your Telegram (or press Enter to cancel): "
if "!PAIR_CODE!"=="" (
    echo [!] Cancelled.
    timeout /t 2 >nul
    goto SHOW_MENU
)
echo [*] Sending pairing approval...
docker exec -it isa_ai_analyst openclaw pairing approve telegram !PAIR_CODE!
pause
goto SHOW_MENU

:EXIT
exit /b 0

:: -----------------------------------------------
:: SUBROUTINE: Write a key to .env
:: Usage: call :WRITE_KEY KEY_NAME VALUE
:: -----------------------------------------------
:WRITE_KEY
set _KEY=%~1
set _VAL=%~2
:: Remove existing line with this key, then append updated value
findstr /v /r "^%_KEY%=" .env > .env.tmp 2>nul
if exist .env.tmp (
    move /y .env.tmp .env >nul
)
echo %_KEY%=%_VAL%>> .env
exit /b
