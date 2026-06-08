@echo off
echo File Event: %EVENT_TYPE%
echo Source Path: %SRC_PATH%
echo Dest Path: %DEST_PATH%
echo Event Time: %EVENT_TIME%
echo. >> file_events.log
echo [%EVENT_TIME%] %EVENT_TYPE%: %SRC_PATH% >> file_events.log
