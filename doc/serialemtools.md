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

In this example, we like to order the Navigator File that is currently open in SerialEM. This requires that the Python environment that contains the py-EM installation is executed and calls the desired function.

In order to run the python environment, you need to define it in a batch file. A template is provided [here].