@echo off
setlocal EnableExtensions DisableDelayedExpansion
cd /d "%~dp0"
rem Never stop an interactive batch update inside Git's less/more pager.
set "GIT_PAGER=cat"
set "PAGER=cat"
if /i "%~1"=="--help" goto help
if not "%~2"=="" goto help
set "GEOAI_COMMIT_MESSAGE=Update GeoAI website"
if not "%~1"=="" set "GEOAI_COMMIT_MESSAGE=%~1"
where git >nul 2>&1
if errorlevel 1 goto failed
git --no-pager rev-parse --show-toplevel >nul 2>&1
if errorlevel 1 goto failed
git --no-pager symbolic-ref --quiet --short HEAD
if errorlevel 1 (
  echo Switch to a branch before updating GitHub.
  goto failed
)
git --no-pager remote get-url origin
if errorlevel 1 goto failed
if /i "%~1"=="--preview" goto previewOnly
set "GEOAI_INDEX_LOCK="
for /f "delims=" %%L in ('git --no-pager rev-parse --git-path index.lock') do set "GEOAI_INDEX_LOCK=%%L"
if defined GEOAI_INDEX_LOCK if exist "%GEOAI_INDEX_LOCK%" (
  echo Git's index is locked by another operation or an interrupted Git command.
  echo Close other Git operations before retrying. Lock: %GEOAI_INDEX_LOCK%
  goto failed
)
rem Allow removal of previously tracked caches; block cache content being published.
git --no-pager diff --cached --quiet --diff-filter=ACMRTUXB -- "frontend/.next*" ".cache/**"
if errorlevel 2 goto failed
if errorlevel 1 (
  echo Generated cache additions or modifications are staged. Unstage those files before continuing.
  goto failed
)
git --no-pager config user.name >nul 2>&1
if errorlevel 1 (
  echo Git author name is missing. Configure git config user.name before publishing.
  goto failed
)
git --no-pager config user.email >nul 2>&1
if errorlevel 1 (
  echo Git author email is missing. Configure git config user.email before publishing.
  goto failed
)
set "GEOAI_CONFLICTS="
for /f "delims=" %%F in ('git --no-pager diff --name-only --diff-filter^=U') do set "GEOAI_CONFLICTS=1"
if defined GEOAI_CONFLICTS (
  echo Resolve the existing merge conflicts before publishing.
  goto failed
)
echo Checking the current remote state...
git --no-pager fetch origin
if errorlevel 1 goto failed
set "GEOAI_BRANCH="
for /f "delims=" %%B in ('git --no-pager symbolic-ref --quiet --short HEAD') do set "GEOAI_BRANCH=%%B"
git --no-pager show-ref --verify --quiet "refs/remotes/origin/%GEOAI_BRANCH%"
if errorlevel 1 goto preview
git --no-pager merge-base --is-ancestor "origin/%GEOAI_BRANCH%" HEAD
if errorlevel 1 (
  echo The remote branch contains commits missing locally.
  echo Merge or rebase those changes before running this updater again.
  goto failed
)

:preview
rem Default action is publish; --preview remains read-only.
goto publish

:publish
echo Staging website changes. Large projects may take a moment...
rem .gitignore excludes generated files; explicit exclusions trigger ignored-path errors.
git -c core.safecrlf=false --no-pager add -A
if errorlevel 1 goto failed
rem Check again after staging in case tracked cache content was modified.
git --no-pager diff --cached --quiet --diff-filter=ACMRTUXB -- "frontend/.next*" ".cache/**"
if errorlevel 2 goto failed
if errorlevel 1 (
  echo Generated cache content is staged. Unstage it before publishing.
  goto failed
)
git --no-pager diff --cached --quiet
if errorlevel 2 goto failed
if not errorlevel 1 goto push
echo Committing website changes...
git --no-pager commit --quiet -m "%GEOAI_COMMIT_MESSAGE%"
if errorlevel 1 goto failed

:push
echo Pushing code to GitHub...
git --no-pager push --progress -u origin HEAD
if errorlevel 1 goto failed
echo.
echo GitHub update complete.
echo Branch: %GEOAI_BRANCH%
pause
exit /b 0

:previewOnly
echo Local project changes:
git --no-pager diff HEAD --stat --stat-count=12 -- . ":(exclude)frontend/.next*" ":(exclude).cache/**"
if errorlevel 1 goto failed
echo New files and folders:
git --no-pager ls-files --others --exclude-standard --directory -- . ":(exclude)frontend/.next*" ":(exclude).cache/**"
if errorlevel 1 goto failed
echo.
echo Already staged changes:
git --no-pager diff --cached --stat --stat-count=8
exit /b %errorlevel%

:help
echo Usage: github-update.bat ["commit message" ^| --preview ^| --help]
echo --preview shows local changes without fetching, staging, committing or pushing.
echo Double-click to stage project changes, commit, and push the current branch.
echo No confirmation is required. Requires GitHub authentication.
echo Generated Next.js caches are excluded; staged cache deletions are allowed.
echo No force push is used.
exit /b 0

:failed
echo.
echo GitHub update failed. Check the error above.
echo If the remote has newer commits, reconcile them before running this again.
pause
exit /b 1
