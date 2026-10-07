@echo off
setlocal
rem Opens the Red Frontier facility in Blender, looking through the Hangar entrance camera.
rem In the 3D view: keys 1-4 Hangar cameras, 5-8 Mission Control, 9 Mars Intelligence, 0 = free look. Please don't save changes (files are rebuilt from scripts).
if not defined BLENDER_EXE set "BLENDER_EXE=blender.exe"
where.exe "%BLENDER_EXE%" >nul 2>&1
if errorlevel 1 (
	echo Blender was not found. Add blender.exe to PATH or set BLENDER_EXE to its full path.
	exit /b 1
)
set TEMP=%~dp0tmp
set TMP=%~dp0tmp
start "" "%BLENDER_EXE%" "%~dp0blender\RF_Facility.blend" --python "%~dp0scripts\open_viewer.py"
endlocal
