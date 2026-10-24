@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
if /i "%~1"=="--help" goto help
if not "%~1"=="" if /i not "%~1"=="backend" if /i not "%~1"=="frontend" goto help
if /i "%~1"=="backend" goto backend
where node >nul 2>&1
if errorlevel 1 (
  echo Node.js is missing from PATH. Install Node.js 20.9 or newer.
  goto failed
)
where npm >nul 2>&1
if errorlevel 1 (
  echo npm is missing from PATH. Reinstall Node.js with npm included.
  goto failed
)
node -e "const [major, minor] = process.versions.node.split('.').map(Number); process.exit(major < 20 || (major === 20 && minor < 9) ? 1 : 0)"
if errorlevel 1 (
  echo This Next.js website requires Node.js 20.9 or newer.
  goto failed
)
if /i "%~1"=="frontend" goto checkFrontend
if not exist "backend\.venv\Scripts\python.exe" goto missing
if /i "%~1"=="backend" goto backend
:checkFrontend
if not exist "frontend\node_modules\next\package.json" goto missing
if not exist "%~dp0start-copilot-review.ps1" goto missing
if not exist "backend\scripts\serve_copilot_review_local.py" goto missing
rem Run the website's predev lifecycle even when the PowerShell launcher invokes Next directly.
pushd "%~dp0frontend"
call npm run predev
if errorlevel 1 (
  popd
  goto failed
)
popd
if /i "%~1"=="backend" goto backend
if /i "%~1"=="frontend" goto frontend
rem Local offline review: backend 8001, same-origin frontend 3001.
rem Wait for backend readiness. No automatic installs or paid inference.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-copilot-review.ps1"
if errorlevel 1 goto failed
exit /b 0

:backend
call "%~dp0run-backend.bat"
exit /b %errorlevel%

:frontend
powershell -NoProfile -Command "try { if ((Invoke-RestMethod 'http://127.0.0.1:8001/api/health' -TimeoutSec 3).status -ne 'ok') { exit 1 } } catch { exit 1 }"
if errorlevel 1 (
  echo Start run-website.bat backend first, or use run-website.bat without arguments.
  exit /b 1
)
cd frontend
set "GEOAI_LOCAL_REVIEW=true"
set "NEXT_PUBLIC_API_URL=/local-api"
call npm run dev --ignore-scripts
exit /b %errorlevel%

:missing
echo Local dependencies or startup scripts are missing. See LOCAL_SETUP.md.
echo Required: backend\.venv, frontend\node_modules, and start-copilot-review.ps1.
echo Setup: cd backend and install requirements.txt into .venv.
echo Setup: cd frontend and run npm ci.
goto failed

:help
echo Usage: run-website.bat [backend^|frontend^|--help]
echo Without arguments: start or reuse the local API and website.
echo Website: http://localhost:3001
echo API docs: http://localhost:8001/docs
echo Press Ctrl+C to stop the foreground server.
exit /b 0

:failed
echo Startup failed. Review the error above.
if "%~1"=="" pause
exit /b 1
