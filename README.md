## Overview

md-rec automatically records, labels and marks tracks on compatible Sony MiniDisc recorders without NetMD.

Currently tested models: MZ-R90, MZ-R91

## Components

- [Foobar2000](https://www.foobar2000.org/) (Windows) or [DeaDBeeF](https://deadbeef.sourceforge.io/) (Linux) music player with [beefweb](https://github.com/hyperblast/beefweb) plugin
- Raspberry Pi Zero W (or similar) running the md-rec script
- interface circuit with a digital potentiometer ([MCP4251-503](https://www.microchip.com/wwwproducts/en/MCP4251) or similar)

## How it works

md-rec script uses an API provided by the beefweb plugin to remotely control a compatible music player on a PC. It grabs the track names from a playlist and breaks them down into a sequence of button presses. These are subsequently translated by the interface circuit into signals recognized by the MD recorder. The script then inserts a Track Mark at end of a track and proceeds with the next item on the playlist.

```
 ----------
|          | <---audio--- [PC] <---REST---> [Raspberry Pi]
| Sony MD  |                                     |
| Recorder |                                     |
|          | <-------- [MCP4251] <------SPI-------
 ----------
 ```
## Interface circuit

The circuit simulates a button press by changing resistance between pin 2 and 4 of the remote connector. It is controlled by the Raspberry Pi over the Serial Peripheral Interface (SPI). It is designed to use a minimum of components and be very easy to build.

![MDPlug](https://user-images.githubusercontent.com/75824/124729455-bee3c100-df10-11eb-86da-0c182e939873.png) 

You can salvage a connector from a broken remote, use a piece of thin PCB with correctly spaced traces or hook up your circuit directly using springy pins such as [these](https://botland.store/connectors-raster-254-mm/6889-pin-for-case-raster254mm-10pcs.html).

MCP4251-503 was selected as the IC for this project due to its low cost (~$2), good availiability and a DIP package option. It is an 8-bit, 2-channel digital potentiometer acting as a 100-50k Ohm rheostat. Both channels are used in parallel for greater precision and lower 'resting' resistance. More about suitable chips [on a separate wiki page](https://github.com/fijam/md-rec/wiki/IC-choice). 

### Bill of materials

	one MCP4251-503 digital potentiometer in a DIP package
	one 0.1uF decoupling capacitor
	one 10k Ohm pull-down resistor
	a breadboard
	some jumper wires

### Schematics

![mcp](https://user-images.githubusercontent.com/75824/124385086-93749280-dcd4-11eb-975d-0333a9a299c7.png)![circuit](https://user-images.githubusercontent.com/75824/124750990-6a4b4080-df26-11eb-8a8f-61b44d9fd752.jpg)


## Requirements

To install the required dependencies on Raspberry Pi OS:

```
apt-get install python3-spidev python3-unidecode python3-requests python3-rpi.gpio python3-yaml
```

## Use

### First time setup

1. Install a music player with the [beefweb](https://github.com/hyperblast/beefweb) plugin on your PC. Enable remote access in the plugin options. 
2. Connect Raspberry Pi to your local network. ([Additional steps for boards without WiFi like Pi Zero.](https://github.com/fijam/md-rec/wiki/Networking-with-Windows-over-USB)).
3. Log in to Raspberry Pi and create a settings file with `./configurator.py`
4. Enable SPI with [raspi-config](https://www.raspberrypi.org/documentation/configuration/raspi-config.md).

### Recording a MiniDisc

1. Connect your PC audio output (toslink or analog) to the input on the MD recorder.
2. Connect the interface circuit to the remote connector on the MD recorder.
3. Log in to Raspberry Pi and run the script with `./md-rec.py`

It is recommended to use the [WASAPI plugin](https://www.foobar2000.org/components/view/foo_out_wasapi) with Foobar2000 to prevent accidental recording of other system sounds.

### Sample output

```
$ ./md-rec.py
> Connect your Sony Recorder and insert a blank MD
Press Enter when ready.
Wait for REC Standby...
> Open up Foobar2000 with the playlist you want to record
Press Enter when ready.
The following tracks will be burned & labelled:
Doctor 3 - Sgt. Pepper's Lonely Hearts Club Band
Total playlist duration: 0:04:50
Press Enter to begin.
Recording: Doctor 3 - Sgt. Pepper's Lonely Hearts Club Band
Track labelled. Time to TMark: 255s
Waiting for TOC to save...
Bye!
```
https://user-images.githubusercontent.com/75824/124761191-d3848100-df31-11eb-93bc-0f6b747f92f4.mp4

## Limitations

Limitations inherent to the MD format:

- up to 254 tracks per disk
- up to ~200 characters per track
- up to ~1700 total characters per disc
- limited character set (ASCII charaters excluding `[ \ ] ^ { | } ~`)

md-rec will automatically turn accented letters in track names into ASCII. This works well for Latin scripts, not so much for Asian scripts.

md-rec will fail if track duration is too short to finish labelling in time for the next track. It takes about 30-40s to label a track.

## Troubleshooting

See the wiki page on [Troubleshooting](https://github.com/fijam/md-rec/wiki/Troubleshooting)

## Contributions welcome

Patches adding the following functionality are welcome:

- support for more recorder models + modularization
- labelling of already-recorded discs - automatic and manual modes
- better error handling

The script is deliberately very simple so that anyone can follow along and make changes as needed. When contributing new code to this project please try to keep it easy to understand.

Reports of successful/unsuccessful use of this script with other Sony models are welcome: MZ-R37, MZ-R55, MZ-R70, MZ-R900, MZ-R700, MZ-R701, MZ-R500

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/fijam)
