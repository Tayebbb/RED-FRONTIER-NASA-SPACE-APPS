@echo off
rem Runs the Red Frontier Hangar viewer in Godot 4.7.
rem Keys: 1-4 Hangar, 5-8 Mission Control, 9 Mars Intelligence, Tab next camera | 0 or hold right mouse = free fly (WASD, Q/E, Shift) | L launch mode | F quality | H help | Esc quit
rem Machine setting: where Godot 4.7 is installed.
set GODOT=D:\Godot_v4.7-stable_win64.exe\Godot_v4.7-stable_win64.exe
start "" "%GODOT%" --path "%~dp0godot"
