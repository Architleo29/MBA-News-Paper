@echo off
cd /d d:\SmartNewspaper
echo ============================================== >> pipeline_run.log
echo Starting SmartNews Pipeline at %date% %time% >> pipeline_run.log
echo ============================================== >> pipeline_run.log
venv\Scripts\python.exe main.py --offline >> pipeline_run.log 2>&1
echo Pipeline execution finished at %date% %time% >> pipeline_run.log
echo ---------------------------------------------- >> pipeline_run.log
