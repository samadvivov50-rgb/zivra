@echo off
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\check-zivra.ps1" %*
