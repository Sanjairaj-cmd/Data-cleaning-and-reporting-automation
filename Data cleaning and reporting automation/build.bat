@echo off
echo =======================================================
echo Building Marvel Avengers Hanging Animations Executable
echo =======================================================

pyinstaller --noconfirm MarvelAvengersHanging.spec

echo.
if exist "dist\MarvelAvengersHanging\MarvelAvengersHanging.exe" (
    echo =======================================================
    echo BUILD SUCCESSFUL!
    echo Executable created at:
    echo dist\MarvelAvengersHanging\MarvelAvengersHanging.exe
    echo =======================================================
) else (
    echo =======================================================
    echo BUILD FAILED! Check output above for details.
    echo =======================================================
)
pause
