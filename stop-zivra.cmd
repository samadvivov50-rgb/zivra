@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\stop-zivra.ps1" %*
