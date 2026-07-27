@echo off
set CONDA_ACTIVATE="%USERPROFILE%\anaconda3\Scripts\activate.bat"
call %CONDA_ACTIVATE% agente_ia
pip install -r requirements.txt
