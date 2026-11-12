@echo off
setlocal
cd /d %~dp0
py -3 -m venv .build-venv
call .build-venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-client.txt pyinstaller
pyinstaller --noconfirm --clean Wasap.spec
if not exist dist\Wasap\config mkdir dist\Wasap\config
if not exist dist\Wasap\config\client.env copy config\client.env.example dist\Wasap\config\client.env
echo.
echo Aplicacion generada en dist\Wasap\Wasap.exe
pause
