### Note: A new version which does not require a Raspberry Pi for operation is available here: https://github.com/fijam/gmdrec

## Overview

md-rec automatically records, labels and marks tracks on compatible Sony MiniDisc recorders without NetMD.

Currently tested models: MZ-R90, MZ-R91

## Components

- [Foobar2000](https://www.foobar2000.org/) (Windows) or [DeaDBeeF](https://deadbeef.sourceforge.io/) (Linux/macOS) music player with [beefweb](https://github.com/hyperblast/beefweb) plugin
- Raspberry Pi Zero W (or similar) running the md-rec script
- interface circuit with a digital potentiometer ([MCP4251-503](https://www.microchip.com/wwwproducts/en/MCP4251) or similar)

## How it works

md-rec script uses an API provided by the beefweb plugin to remotely control a compatible music player on a PC. It grabs the track names from a playlist and breaks them down into a sequence of button presses. These are translated by the interface circuit into signals recognized by the MD recorder. 

```
 ----------
|          | <---audio--- [PC] <---REST---> [Raspberry Pi]
| Sony MD  |                                     |
| Recorder |                                     |
|          | <-------- [MCP4251] <------SPI-------
 ----------
 ```
## Interface circuit

The circuit simulates a button press by changing resistance between pin 2 and 4 of the remote connector. You also need to connect the digital ground which is on pin 1. The pin order on the remote connector is: mini jack, 1, 2, 3, 4. Pin 3 controls the remote display and is unused.

You can salvage a connector from a broken remote, use a piece of thin PCB with correctly spaced traces or hook up your circuit directly using springy pins such as [these](https://botland.store/connectors-raster-254-mm/6889-pin-for-case-raster254mm-10pcs.html).

I selected MCP4251-503 for this project due to its low cost (~$2), good availiability and a DIP package option. It is a 50k Ohm, 8-bit, 2-channel digital potentiometer. It communicates with Raspberry Pi over SPI.

More about suitable chips [on a separate wiki page](https://github.com/fijam/md-rec/wiki/IC-choice). 

### Bill of materials

	one MCP4251-503 digital potentiometer in a DIP package
	one 0.1uF decoupling capacitor
	one 10k Ohm pull-down resistor
	a breadboard
	some jumper wires

### Schematics

![md-rec-scheme-2](https://user-images.githubusercontent.com/75824/134492103-87766ddb-2c5f-476a-93d0-dde07fdb5773.png)


## Requirements

To install the required dependencies on Raspberry Pi OS:

```
apt-get install python3-spidev python3-unidecode python3-requests python3-rpi.gpio python3-yaml
```

## Usage

```
usage: md-rec.py [-h] [--conf [CONF]] [--no-tmarks] [--mode {hand,stdin}]

optional arguments:
  -h, --help           show this help message and exit
  --conf [CONF]        Name of the configuration file
  --no-tmarks          Do not enter track marks automatically
  --mode {hand,stdin}  Select manual labelling mode
```

### First time setup

1. Install a music player with the [beefweb](https://github.com/hyperblast/beefweb) plugin on your PC. Enable remote access in the plugin options. 
2. Connect Raspberry Pi to your local network. ([Additional steps for boards without WiFi like Pi Zero.](https://github.com/fijam/md-rec/wiki/Networking-with-Windows-over-USB)).
3. Log in to Raspberry Pi and create a settings file with `./configurator.py`
4. Enable SPI with [raspi-config](https://www.raspberrypi.org/documentation/configuration/raspi-config.md).

### Recording a MiniDisc

1. Connect your PC audio output (toslink or analog) to the input on the MD recorder.
2. Connect the interface circuit to the remote connector on the MD recorder.
3. Log in to Raspberry Pi and run the interactive script with `./md-rec.py`

Consider using the [WASAPI plugin](https://www.foobar2000.org/components/view/foo_out_wasapi) with Foobar2000 to prevent accidental recording of other system sounds.

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

### Labelling a recorded MiniDisc by hand

With `./md-rec.py --mode hand` you can manually label an already-recorded MiniDisc by hand, one track at a time.

### Reading track names from stdin

With `./md-rec.py --mode stdin` you can integrate md-rec with your own software. Any newline-terminated string piped in will be sanitized to ASCII and saved. Send EOF to exit. No interactive prompts in this mode.

## Limitations

Limitations inherent to the MD format:

- up to 254 tracks per disk
- up to ~200 characters per track
- up to ~1700 total characters per disc
- limited character set (ASCII charaters excluding `[ \ ] ^ { | } ~`)

md-rec will automatically turn accented letters in track names into ASCII. This works well for Latin scripts, not so much for Asian scripts.

md-rec will fail if track duration is too short to finish labelling in time for the next track. It takes about 30-40s to label a track.

In automatic mode (default) there may be duplicate TMarks entered by both the script and the recorder. See https://github.com/fijam/md-rec/issues/2 for possible workarounds.

## Troubleshooting

See the wiki page on [Troubleshooting](https://github.com/fijam/md-rec/wiki/Troubleshooting)

## Contributions welcome

Merge requests providing new functionality are welcome. The script is deliberately very simple so that anyone can follow along and make changes as needed. When contributing to this project please try to keep it easy to understand.

Please report successful/unsuccessful use of this script with other Sony models: MZ-R37, MZ-R55, MZ-R70, MZ-R900, MZ-R700, MZ-R701, MZ-R500

[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/fijam)
