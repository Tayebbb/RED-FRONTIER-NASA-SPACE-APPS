@echo off
setlocal
rem Runs the Red Frontier Hangar viewer in Godot 4.7.
rem Keys: 1-4 Hangar, 5-8 Mission Control, 9 Mars Intelligence, Tab next camera | 0 or hold right mouse = free fly (WASD, Q/E, Shift) | L launch mode | F quality | H help | Esc quit
if not defined GODOT_EXE set "GODOT_EXE=godot.exe"
where.exe "%GODOT_EXE%" >nul 2>&1
if errorlevel 1 (
	echo Godot 4.7 was not found. Add godot.exe to PATH or set GODOT_EXE to its full path.
	exit /b 1
)
start "" "%GODOT_EXE%" --path "%~dp0godot" res://viewer/hangar_viewer.tscn
endlocal
