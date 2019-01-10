## Setting up integration in SerialEM GUI

SerialEM comes with the capability of launching external command from its graphical user interface (GUI).
A detailed description of how this integration works can be found [here](https://bio3d.colorado.edu/SerialEM/hlp/html/menu_tools.htm "Tools Menu - SerialEM Help").

In order to enable the menu that shows external tools, a section needs to be added to [SerialEM's property file](https://bio3d.colorado.edu/SerialEM/hlp/html//about_properties.htm "Property files - SerialEM Help"), that specifies the tools and the commands that should be run.

This set of propeties:
```
ExternalTool Open Nav File
ToolCommand 1 notepad
ToolArguments 1 %navfile%
```
would open the currently active Navigator file in a text editor. 

### Example: Sort current Navigator

In this example, we like to order the Navigator File that is currently open in SerialEM. This requires that the Python environment that contains the py-EM installation is executed and calls the desired function.

#### define py-EM specific python launcher

In order to run the python environment, you need to define it in a batch file. A template is provided [here](https://git.embl.de/schorb/pyem/raw/master/tutorials/callpython.bat?inline=false) (if it opens inside the browser, use "save link as...").

You need to change the first line of this script to point to your Anaconda installation/environment that hosts py-EM. In a default installation (for a single user), you might just need to replace the user name.
```
set root=C:\Users\YOURUSER\Anaconda3
```

The python script we like to run contains the functionality described in [Tutorial 1](https://git.embl.de/schorb/pyem/tree/master#tutorials) and you can download it from [here](https://git.embl.de/schorb/pyem/raw/master/applications/sortnav.py?inline=false) (if it opens inside the browser, use "save link as...").

#### add script to SerialEM's Tools Menu

We now need to [add the parameters to run this script](https://bio3d.colorado.edu/SerialEM/hlp/html/menu_tools.htm "Tools Menu - SerialEM Help") using the python caller from above to [SerialEM's property file](https://bio3d.colorado.edu/SerialEM/hlp/html//about_properties.htm "Property files - SerialEM Help").

```
ExternalTool Sort Navigator
ToolCommand 4  C:\scripts\callpython.bat
ToolArguments 4 C:\scripts\sortnav.py %navfile%
```

Where C:\scripts needs to be replaced with the directory of your scripts and the index of the tool call (here: 4) should simply add to any tools that are already listed.

When you now start SerialEM, there should be a "Tools" Menu appearing that hosts all the external commands you have defined.
![Tools Menu](https://git.embl.de/schorb/pyem/raw/master/doc/images/serialemtools.png)

You can now run the procedure by clicking this menu entry

![Running scipt](https://git.embl.de/schorb/pyem/raw/master/doc/images/sortnav.png)

and the sorted Navigator file will appear in the same directory as the current one.

