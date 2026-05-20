@echo off
chcp 65001 >nul
cd /d D:\Water\shuiyuan
echo ========================================
echo   Usagi Auto-Reply Loop
echo ========================================
echo.

:loop
echo [%date% %time%] Starting conversation loop...
uv run python conversation_loop.py --topic-id 475459 --auto --interval 120 --max-replies-per-run 5
echo [%date% %time%] Loop exited. Restarting in 10 seconds...
timeout /t 10 /nobreak >nul
goto loop
