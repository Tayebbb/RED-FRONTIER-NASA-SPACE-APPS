@echo off
rem Opens the Red Frontier facility in Blender, looking through the Hangar entrance camera.
rem In the 3D view: keys 1-4 switch cameras, 0 = free look. Please don't save changes (files are rebuilt from scripts).
set TEMP=D:\RedFrontier\tmp
set TMP=D:\RedFrontier\tmp
start "" "D:\tools\blender.exe" "D:\RedFrontier\blender\RF_Facility.blend" --python "D:\RedFrontier\scripts\open_viewer.py"
