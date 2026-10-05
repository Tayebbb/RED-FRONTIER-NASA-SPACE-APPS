@echo off
rem Opens the Red Frontier facility in Blender, looking through the Hangar entrance camera.
rem In the 3D view: keys 1-4 Hangar cameras, 5-8 Mission Control, 9 Mars Intelligence, 0 = free look. Please don't save changes (files are rebuilt from scripts).
rem Machine setting: where Blender is installed.
set BLENDER=D:\tools\blender.exe
set TEMP=%~dp0tmp
set TMP=%~dp0tmp
start "" "%BLENDER%" "%~dp0blender\RF_Facility.blend" --python "%~dp0scripts\open_viewer.py"
