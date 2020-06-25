## Setting up Icy integration to register two maps<a name="icy"></a>

Install Icy. Change the path to icy (`icypath`) in the script file `clem_icy.py`.
Download this [icy script file](https://git.embl.de/schorb/pyem/raw/master/tutorials/opener.js?inline=false) and change the path pointing to it (`scriptpath`) in the script file `clem_icy.py`.

#### Integrate into SerialEM

Follow the instructions on [setting up integration in SerialEM GUI](https://git.embl.de/schorb/pyem/blob/master/doc/serialemtools.md) to integrate the script file `clem_icy.py`.

## Register two maps in Icy/ec-CLEM

- Select the two maps you like to register for **Acquire**. You can already provide initial registration points if you like. These will be passed on to Icy.

- Start the Icy Tool in SerialEM.

- Start ec-CLEM and register the two images.

- when done, make sure to click **"Show ROIs on original source image"**. It is faster if you do this before updating the transformation.

- close icy

- you will now have a Navigator File `xxx_icy.nav` that contains your landmarks as SerialEM registration points.
