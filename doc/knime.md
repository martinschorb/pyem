## Setting up KNIME<a name="knime"></a>

Install KNIME from [here](https://www.knime.com/downloads/download-knime)

#### enable commity nodes

Open KNIME Preferences. ("File > Preferences")
![KNIME preferences](https://git.embl.de/schorb/pyem/raw/master/doc/images/knime_pref.png)


In "Install/Update > Available Software Sites", select "Stable Community Contributions" and check that "Community Contributions" is also active. 

![KNIME updates](https://git.embl.de/schorb/pyem/raw/master/doc/images/knime_updates.png)


#### setting up the Python integration

In the Preferences, go to "KNIME > Python". Provide the location of the python binary executable files of your Anaconda installation. Default location in Windows would be for example: `C:\Anaconda2\python.exe`. Do this for your Python version of choice and make sure you select this version as "Default". A successful integration should show no red warning messages but simply read the version number.

![KNIME Python](https://git.embl.de/schorb/pyem/raw/master/doc/images/knime_python.png)


Import the desired workflow from [here](https://git.embl.de/schorb/pyem/tree/master/knime). KNIME will now ask you if it should fetch the necessary nodes from its repositories. Install all of them and the KNIME workflow should run as it is.


In the Python nodes, you need to select the Python version the node should use. If you create your own workflows, this is set to what you chose as default. If you download a workflow, you might have to change it.

![KNIME Python_node](https://git.embl.de/schorb/pyem/raw/master/doc/images/knime_pynode.png)