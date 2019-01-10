## Setting up integration in SerialEM GUI

SerialEM comes with the capability of launching external command from its graphical user interface (GUI).
A detailed description of how this integration works can be found [here](https://bio3d.colorado.edu/SerialEM/hlp/html/menu_tools.htm "Tools Menu - SerialEM Help").

In order to enable the menu that shows external tools, a section needs to be added to [SerialEM's property file](https://bio3d.colorado.edu/SerialEM/hlp/html//about_properties.htm "Property files - SerialEM Help"), that specifies the tools and the commands that should be run.

This command:
```
ExternalTool Open Nav File
ToolCommand 2 notepad
ToolArguments 2 %navfile%
```
would open the currently active Navigator file in a text editor. 