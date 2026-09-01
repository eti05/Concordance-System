@echo off
REM Double click this file on Windows to remove everything this project created.
REM
REM It removes the Oracle container, the Docker volume holding the loaded corpus,
REM and the local virtual environment. It asks for confirmation first, and it
REM never touches the project's own files.

cd /d "%~dp0"
call run.bat --clean
