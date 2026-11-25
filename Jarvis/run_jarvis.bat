@echo off
echo.
echo  ========================================
echo  JARVIS - Career Command Centre Launcher
echo  ========================================
echo.
echo  Starting JARVIS... opening in browser.
echo  Press Ctrl+C in this window to stop.
echo.
streamlit run app.py --server.headless false
pause
