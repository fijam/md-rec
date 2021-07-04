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

MCP4251-503 was selected as the IC for this project due to its low cost (~$2), good availiability and a DIP package option. It is an 8-bit, 2-channel digital potentiometer acting as a 100-50k Ohm rheostat. Both channels are used in parallel for greater precision and lower 'resting' resistance. 
MCP4261-503 can be a drop-in substitute. 

### Bill of materials

	one MCP4251-503 digital potentiometer in a DIP package
	one 0.1uF decoupling capacitor
	one 10k Ohm pull-down resistor
	a breadboard
	some jumper wires

### Schematics

![mcp](https://user-images.githubusercontent.com/75824/124385086-93749280-dcd4-11eb-975d-0333a9a299c7.png)

## Requirements

	Python 3.7
	spidev
	RPi.GPIO
	requests
	unidecode

To install the required dependencies on Raspberry Pi OS:

```
apt-get install python3-spidev python3-unidecode python3-requests python3-rpi.gpio
```

## Use

### First time setup

1. Install a supported music player along with the [beefweb](https://github.com/hyperblast/beefweb) plugin on your PC. Enable remote access in the plugin options. 
2. Connect Raspberry Pi to your local network. (Additional steps for boards without WiFi like Pi Zero.)
3. Log in to Raspberry Pi and create a settings file with `./configurator.py`

### Recording a MD

1. Connect your PC audio output (toslink or analog) to the input on the MD recorder
2. Connect the interface circuit to the remote connector on the MD recorder
3. Log in to Raspberry Pi and run the script with `./md-rec.py`

It is recommended to use the [WASAPI plugin](https://www.foobar2000.org/components/view/foo_out_wasapi) with Foobar2000 to prevent accidental recording of other system sounds.

## Limitations

Limitations inherent to the MD format:

- up to 254 tracks per disk
- up to ~200 characters per track
- up to ~1700 total characters per disc
- limited character set (ASCII charaters without "[ \ ] ^ { | } ~")

md-rec will automatically turn accented letters in track names into ASCII. This works well for Latin scripts, not so much for Asian scripts.

md-rec will fail if track duration is too short to finish labelling in time for the next track.

## Troubleshooting

### The script hangs when trying to read the playlist:

- Make sure remote access is enabled in beefweb plugin options
- Make sure the beefweb plugin access port is not blocked by a firewall
- Make sure both the PC and Raspberry Pi are on the same local private network
- Make sure the 'host' variable is set correctly
	
### No button presses are registered by the MD recorder:

- Make sure the interface circuit is built correctly
- Make sure Raspberry Pi is connected correctly to the circuit and that SPI works
- Make sure the circuit is connected to the correct pins on the remote controller socket of the MD recorder

### The letters entered are all gibberish:

- Adjust the 'wiper' variables for each button until all button presses are registered correctly
- Increase the value of the 'press' variable to 0.05 or more
	
### TMarks are entered too late:

- Adjust the 'offset' variable to account for network latency

## Contributors guide

The script is deliberately very simple so that anyone can follow along and make changes as needed. When contributing new code to this project please try to keep it easy to understand. Try to use descriptive names for the functions and variables, making the code largely self-documenting. It is OK to be a bit verbose.

### Contributions welcome

Patches adding the following functionality are welcome:

- support for more recorder models + modularization
- labelling of already-recorded discs - automatic and manual modes
- better error handling

Bug reports are welcome

Reports of successful/unsuccessful use of this script with other Sony models are welcome:

- models that need testing: MZ-R37, MZ-R55, MZ-R70, MZ-R900, MZ-R700, MZ-R701, MZ-R500
