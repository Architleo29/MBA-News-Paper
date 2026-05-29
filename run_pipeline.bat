@echo off
cd /d d:\SmartNewspaper
echo ============================================== >> pipeline_run.log
echo Starting SmartNews Pipeline at %date% %time% >> pipeline_run.log
echo ============================================== >> pipeline_run.log
venv\Scripts\python.exe main.py --offline >> pipeline_run.log 2>&1
echo Committing and pushing updates to GitHub... >> pipeline_run.log
git add index.html preference.html .jetro/frames/newsletter_rendered.html >> pipeline_run.log 2>&1
git commit -m "chore: auto-update daily despatches [skip ci]" >> pipeline_run.log 2>&1
git push origin main >> pipeline_run.log 2>&1
echo Git-Ops auto-deploy push completed at %date% %time% >> pipeline_run.log
echo Pipeline execution finished at %date% %time% >> pipeline_run.log
echo ---------------------------------------------- >> pipeline_run.log
