@echo off
cd /d C:\IT\crawltikitrends
call .venv\Scripts\activate
python tiki_crawler\tiki_crawler\upload_datalake\run_and_upload.py
