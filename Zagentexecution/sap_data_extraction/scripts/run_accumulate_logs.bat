@echo off
REM Wrapper for the SAP log accumulator scheduled task (every <=14 days).
REM Must run in the logged-on user's context (P01 is SNC/SSO).
REM Appends a timestamped run log next to the script.
set PYTHONIOENCODING=utf-8
cd /d "C:\Users\jp_lopez\projects\abapobjectscreation\Zagentexecution\sap_data_extraction\scripts"
echo ==== run %DATE% %TIME% ==== >> accumulate_logs_run.log
python accumulate_logs.py >> accumulate_logs_run.log 2>&1
