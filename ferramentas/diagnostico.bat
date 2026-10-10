@echo off
chcp 65001 >nul
cd /d "%~dp0"
python diagnostico_iso.py "..\ISOs\Pitfall - The Lost Expedition (PT-BR).iso" "..\build\Pitfall_PTBR_teste.iso" "..\extraido\Pitfall - The Lost Expedition (PT-BR)"
pause
