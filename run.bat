@echo off
setlocal EnableDelayedExpansion

REM Concordance System - launcher for Windows.
REM
REM   run.bat            start the database, prepare it if needed, open the app
REM   run.bat --reset    rebuild the schema and reload the corpus from scratch
REM   run.bat --stop     stop the database container
REM
REM Requirements: Docker Desktop and Python 3.9+ (the python.org installer
REM includes Tk). Every path is resolved relative to this file.

cd /d "%~dp0"

REM The application user created by docker-compose.yml.
if not defined ORACLE_USER     set "ORACLE_USER=concordance"
if not defined ORACLE_PASSWORD set "ORACLE_PASSWORD=concordance"
if not defined ORACLE_DSN      set "ORACLE_DSN=localhost:1521/FREEPDB1"

set "CONTAINER=concordance-oracle"

if /I "%~1"=="--stop" (
    docker info >nul 2>&1
    if errorlevel 1 (
        echo Docker is not running, so there is nothing to stop.
        pause & exit /b 0
    )
    echo Stopping the database container ...
    docker compose down >nul 2>&1
    echo Done. The loaded data is kept for next time.
    pause & exit /b 0
)

if /I "%~1"=="--clean" (
    echo This removes the database container, the loaded corpus and the local
    echo virtual environment. The project files themselves are not touched.
    set /p "ANSWER=Type 'yes' to continue: "
    if /I not "!ANSWER!"=="yes" (
        echo Cancelled.
        pause & exit /b 0
    )
    docker info >nul 2>&1
    if errorlevel 1 (
        echo Docker is not running, so the container could not be removed.
        echo Start Docker and run this again to remove the data volume.
    ) else (
        echo Removing the container and its data volume ...
        docker compose down --volumes >nul 2>&1
    )
    echo Removing the virtual environment ...
    if exist ".venv" rmdir /s /q ".venv"
    if exist "__pycache__" rmdir /s /q "__pycache__"
    if exist "ui\__pycache__" rmdir /s /q "ui\__pycache__"
    if exist "tests\__pycache__" rmdir /s /q "tests\__pycache__"
    if exist ".pytest_cache" rmdir /s /q ".pytest_cache"
    echo Done. Nothing of this project is left running or stored.
    pause & exit /b 0
)

where docker >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not installed or not on PATH.
    pause & exit /b 1
)

docker info >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is installed but not running. Start Docker Desktop and try again.
    pause & exit /b 1
)

REM ------------------------------------------------------------- python ---
if not exist ".venv\Scripts\python.exe" (
    echo Creating the virtual environment ...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Could not create the virtual environment. Is Python installed?
        pause & exit /b 1
    )
    ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
    ".venv\Scripts\python.exe" -m pip install --quiet -r requirements.txt
)
set "PYTHON=.venv\Scripts\python.exe"

REM Note on Tcl and Tk: a virtual environment on Windows does not carry the
REM Tcl library along, so tkinter cannot find init.tcl and the window never
REM opens. That is handled by scripts\launch.py rather than here, because the
REM path to the Python installation can contain non ASCII characters, which do
REM not survive being captured through a cmd pipe.

REM ----------------------------------------------------------- database ---
echo 1/3  Starting the Oracle database ...
docker compose up -d >nul

echo      Waiting for it to become ready ...
set "STATUS="
set "TRIES=0"

:waitloop
set "STATUS="
for /f "delims=" %%s in ('docker inspect -f "{{.State.Health.Status}}" %CONTAINER% 2^>nul') do set "STATUS=%%s"
if /I "!STATUS!"=="healthy" goto ready
set /a TRIES+=1
if !TRIES! GEQ 90 (
    echo ERROR: The database did not become ready in time.
    echo Run "docker compose logs oracle" to see why.
    pause & exit /b 1
)
timeout /t 5 /nobreak >nul
goto waitloop

:ready

REM ------------------------------------------------------------- schema ---
set "NEEDS_SETUP=0"
if /I "%~1"=="--reset" (
    set "NEEDS_SETUP=1"
) else (
    %PYTHON% -c "import db; db.run_query('SELECT 1 FROM Documents WHERE ROWNUM = 1')" >nul 2>&1
    if errorlevel 1 set "NEEDS_SETUP=1"
)

if "!NEEDS_SETUP!"=="1" (
    echo 2/3  Preparing the database ^(this runs once and takes a minute^) ...
    %PYTHON% scripts\init_db.py
    %PYTHON% scripts\load_corpus.py
) else (
    echo 2/3  The database is already prepared.
)

REM ---------------------------------------------------------------- app ---
echo 3/3  Opening the Concordance System. Look for a new window.
%PYTHON% scripts\launch.py

echo.
echo Closed. Run "run.bat --stop" when you want to shut the database down.
pause
endlocal
