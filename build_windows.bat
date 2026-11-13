@echo off
setlocal
cd /d "%~dp0"
py -3 -m pip install --upgrade pip
py -3 -m pip install -r requirements-client.txt
py -3 -m PyInstaller --noconfirm --clean --windowed --onedir --name Wasap --paths client --collect-all keyring client\main.py
if not exist "dist\Wasap\config" mkdir "dist\Wasap\config"
copy /Y "config\client.env.example" "dist\Wasap\config\client.env.example" >nul
echo.
echo Compilacion terminada. Configura dist\Wasap\config\client.env y abre Wasap.exe.
pause
