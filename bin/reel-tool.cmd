@echo off
rem reel-tool for PowerShell and cmd: same job as the bash script next to this file, no bash needed except for setup.
setlocal
chcp 65001 >nul
set "ROOT=%~dp0.."
if not defined REEL_STUDIO_DATA if defined CLAUDE_PLUGIN_DATA set "REEL_STUDIO_DATA=%CLAUDE_PLUGIN_DATA%"
if not defined REEL_STUDIO_DATA (
  if not defined CLAUDE_CONFIG_DIR set "CLAUDE_CONFIG_DIR=%USERPROFILE%\.claude"
  if exist "%CLAUDE_CONFIG_DIR%\plugins\data\.reel-studio-data" set /p REEL_STUDIO_DATA=<"%CLAUDE_CONFIG_DIR%\plugins\data\.reel-studio-data"
  if not defined REEL_STUDIO_DATA for /d %%d in ("%CLAUDE_CONFIG_DIR%\plugins\data\reel-studio*") do if not defined REEL_STUDIO_DATA set "REEL_STUDIO_DATA=%%d"
)
if not defined REEL_STUDIO_DATA set "REEL_STUDIO_DATA=%USERPROFILE%\.claude\plugins\data\reel-studio-siroxygenfish"
if /i "%~1"=="setup" (
  if exist "%ProgramFiles%\Git\bin\bash.exe" (
    "%ProgramFiles%\Git\bin\bash.exe" "%~dp0reel-tool" %*
  ) else (
    bash "%~dp0reel-tool" %*
  )
  exit /b %errorlevel%
)
if not exist "%REEL_STUDIO_DATA%\env\venv\Scripts\python.exe" (
  echo Reel Studio is not set up yet. Run /reel-setup. 1>&2
  exit /b 3
)
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
"%REEL_STUDIO_DATA%\env\venv\Scripts\python.exe" "%ROOT%\scripts\cli.py" %*
