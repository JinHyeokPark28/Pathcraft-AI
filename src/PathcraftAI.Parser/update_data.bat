@echo off
REM PathcraftAI 데이터 자동 업데이트 스크립트
REM Windows Task Scheduler에서 실행

echo ========================================
echo PathcraftAI Data Update
echo ========================================
echo Time: %date% %time%
echo ========================================

cd /d "%~dp0"

REM POE.Ninja 데이터 수집
echo.
echo [1/2] Updating POE.Ninja data...
.venv\Scripts\python.exe poe_ninja_fetcher.py --collect --league Standard

REM YouTube 빌드 수집 (선택사항)
echo.
echo [2/2] Updating YouTube builds...
.venv\Scripts\python.exe popular_build_collector.py --league Standard --version 3.27

echo.
echo ========================================
echo Update completed!
echo ========================================
pause
