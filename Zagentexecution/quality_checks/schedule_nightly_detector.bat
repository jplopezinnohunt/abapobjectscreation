@echo off
REM ============================================================================
REM Nightly UNESCO FM-PS Pre-flight Detector
REM Runs the committed_vs_available_detector.py + project_risk_classifier.py
REM Captures CSV diff vs prior run; emails alert if new HARD-BLOCK candidates
REM emerge.
REM
REM Schedule via Windows Task Scheduler:
REM   schtasks /create /tn "UNESCO_FMPS_Nightly_Detector" /tr "%~f0" ^
REM     /sc daily /st 02:00 /ru SYSTEM
REM
REM Or via cron-like (Linux/WSL):
REM   0 2 * * *  /c/Users/jp_lopez/projects/abapobjectscreation/Zagentexecution/quality_checks/schedule_nightly_detector.bat
REM
REM Outputs:
REM   - logs\detector_nightly_<YYYYMMDD>.log
REM   - csv\committed_vs_available_<YYYYMMDD>.csv
REM   - csv\project_risk_<YYYYMMDD>.csv
REM   - csv\diff_alert_<YYYYMMDD>.csv  (only if new HARD-BLOCKs vs prior)
REM ============================================================================

setlocal
set PROJECT_ROOT=c:\Users\jp_lopez\projects\abapobjectscreation
set CHECKS_DIR=%PROJECT_ROOT%\Zagentexecution\quality_checks
set LOG_DIR=%PROJECT_ROOT%\Zagentexecution\sap_data_extraction\logs
set CSV_DIR=%PROJECT_ROOT%\Zagentexecution\quality_checks\nightly

if not exist "%CSV_DIR%" mkdir "%CSV_DIR%"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"

set TS=%date:~10,4%%date:~4,2%%date:~7,2%
set LOGFILE=%LOG_DIR%\detector_nightly_%TS%.log

echo [%date% %time%] === Nightly FM-PS detector start === >> "%LOGFILE%"

cd /d "%CHECKS_DIR%"

REM 1. Run committed-vs-available detector
echo [%date% %time%] Running committed_vs_available_detector.py... >> "%LOGFILE%"
python committed_vs_available_detector.py >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
  echo [%date% %time%] ERROR detector_committed_vs_available exit=%errorlevel% >> "%LOGFILE%"
)
copy /Y committed_vs_available_detector.csv "%CSV_DIR%\committed_vs_available_%TS%.csv" >> "%LOGFILE%" 2>&1

REM 2. Run project-risk classifier
echo [%date% %time%] Running project_risk_classifier.py... >> "%LOGFILE%"
python project_risk_classifier.py >> "%LOGFILE%" 2>&1
if %errorlevel% neq 0 (
  echo [%date% %time%] ERROR project_risk_classifier exit=%errorlevel% >> "%LOGFILE%"
)
copy /Y project_risk_classifier.csv "%CSV_DIR%\project_risk_%TS%.csv" >> "%LOGFILE%" 2>&1

REM 3. Diff vs yesterday — find new HARD-BLOCK candidates
echo [%date% %time%] Diffing vs prior day... >> "%LOGFILE%"
python "%CHECKS_DIR%\nightly_diff.py" >> "%LOGFILE%" 2>&1

echo [%date% %time%] === Nightly FM-PS detector complete === >> "%LOGFILE%"
endlocal
