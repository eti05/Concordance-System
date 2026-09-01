@echo off
REM Double click this file on Windows to stop the Concordance System.
REM
REM It stops the Oracle container and frees the memory it was using. The loaded
REM corpus is kept in a Docker volume, so the next start is quick and no data is
REM lost. To delete the data as well, use clean.bat instead.
REM
REM Deliberately self contained: it does not call run.bat, so there is no
REM nesting and nothing that can go wrong on the way.

cd /d "%~dp0"

docker info >nul 2>&1
if errorlevel 1 goto notrunning

echo Stopping the database container ...
docker compose down
echo.
echo Done. The loaded corpus is kept for next time.
pause
exit /b 0

:notrunning
echo Docker is not running, so there is nothing to stop.
pause
exit /b 0
