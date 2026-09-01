@echo off
REM Double click this file on Windows to remove everything this project created.
REM
REM It removes the Oracle container, the Docker volume holding the loaded corpus,
REM and the local virtual environment. It asks for confirmation first, and it
REM never touches the project's own files.
REM
REM Deliberately self contained: it does not call run.bat, so there is no
REM nesting and nothing that can go wrong on the way.

cd /d "%~dp0"

echo This removes the database container, the loaded corpus and the local
echo virtual environment. The project files themselves are not touched.
echo.
set "ANSWER="
set /p "ANSWER=Type yes to continue: "
if /I not "%ANSWER%"=="yes" goto cancelled

docker info >nul 2>&1
if errorlevel 1 goto nodocker

echo Removing the container and its data volume ...
docker compose down --volumes
goto removefiles

:nodocker
echo Docker is not running, so the container could not be removed.
echo Start Docker and run this again to remove the data volume.

:removefiles
echo Removing the virtual environment ...
if exist ".venv"             rmdir /s /q ".venv"
if exist "__pycache__"       rmdir /s /q "__pycache__"
if exist "ui\__pycache__"    rmdir /s /q "ui\__pycache__"
if exist "tests\__pycache__" rmdir /s /q "tests\__pycache__"
if exist "scripts\__pycache__" rmdir /s /q "scripts\__pycache__"
if exist ".pytest_cache"     rmdir /s /q ".pytest_cache"
echo.
echo Done. Nothing of this project is left running or stored.
pause
exit /b 0

:cancelled
echo Cancelled. Nothing was changed.
pause
exit /b 0
