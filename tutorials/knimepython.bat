@REM Adapt the directory in the PATH to your system's anaconda installation    
  @SET PATH=C:\User\YOURUSER\Anaconda3\Scripts;%PATH%  
  @CALL activate base || ECHO Activating anaconda failed  
  @python %*