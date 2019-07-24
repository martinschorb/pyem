@echo off

set root=C:\Users\YOURUSER\Anaconda3


call %root%\Scripts\activate.bat %root%

call python %1 %2 %3 %4


echo Execution ended, will close this prompt in 10 seconds...

timeout /T 10

exit
