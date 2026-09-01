@echo off
REM Double click this file on Windows to stop the Concordance System.
REM
REM It stops the Oracle container and frees the memory it was using. The loaded
REM corpus is kept in a Docker volume, so the next start is quick and no data is
REM lost. To delete the data as well, use clean.bat instead.

cd /d "%~dp0"
call run.bat --stop
