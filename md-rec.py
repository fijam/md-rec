#!/usr/bin/python3
#pylint: disable=missing-docstring
#pylint: disable-msg=C0103
#pylint: disable=E1101
import sys
import argparse
import time
import datetime
import yaml
import requests
import RPi.GPIO as GPIO
from unidecode import unidecode
import spidev

# functions
def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument('--conf', dest='conf', nargs='?', const='settings.conf',
                        default='settings.conf', action='store',
                        help='Name of the configuration file')
    parser.add_argument('--no-tmarks', dest='no_tmarks', action='store_true',
                        help='Do not enter track marks automatically')
    parser.add_argument('--mode', choices=['hand', 'stdin'], dest='mode',
                        help='Select manual labelling mode')
    return parser.parse_args()

def request_playlist_info():
    response = requests.get(settings['server_url'] + '/api/playlists')
    # return a tuple of playlist ID and number of tracks
    return response.json()['playlists'][0]['id'], response.json()['playlists'][0]['itemCount']

def request_playlist_content(playlist_tuple):
    t_list = []
    total_time = 0
    item_count = playlist_tuple[1]
    payload = {'playlists':'true', 'playlistItems':'true',
               'plref':playlist_tuple[0], 'plrange':'0:'+str(item_count),
               'plcolumns':'%artist% - %title%, %length_seconds%'}
    response = requests.get(settings['server_url']+'/api/query', params=payload)

    for i in range(item_count):
        ascii_track_name = unidecode(response.json()['playlistItems']['items'][i]['columns'][0])
        if not silent_track(ascii_track_name):
            print(ascii_track_name)
        t_list.append(ascii_track_name)
        total_time += int(response.json()['playlistItems']['items'][i]['columns'][1])
    print(f'Total playlist duration: {datetime.timedelta(seconds=total_time)}')
    if total_time >= 4800:
        print('Warning: duration exceeds 80 minutes!')
    if item_count > 254:
        print('Warning: cannot record more than 254 tracks!')
    # return a list of tracks to label
    return t_list

def request_track_remaining():
    response = requests.get(settings['server_url'] + '/api/player')
    remaining = (response.json()['player']['activeItem']['duration']
                 - response.json()['player']['activeItem']['position'])
    # return remaining time in track (in seconds)
    return remaining

def set_mode_play(playlist_tuple):
    requests.post(settings['server_url'] + '/api/player', params={'isMuted':'false', 'playbackMode':'0'})
    requests.post(settings['server_url'] + '/api/player/play/' + playlist_tuple[0]+'/0')

def set_stop():
    requests.post(settings['server_url'] + '/api/player/stop')

def silent_track(track_name):
    if track_name.casefold() == 'silence - silence':
        return True
    return False

def find_distance(letter):
    # find shortest distance to first letter of any charset from either direction
    dist_dict = {}
    for entry in settings['c_entrypoints']:
        search_right = (settings['c_complete'].index(letter) - settings['c_entrypoints'][entry]) % len(settings['c_complete'])
        search_left = (settings['c_complete'].index(letter) - settings['c_entrypoints'][entry]) % -len(settings['c_complete'])
        dist_dict[entry] = min(search_right, search_left, key=abs) # compare absolute, return signed
    return dist_dict

def return_current_set(letter, current_set):
    if letter in settings['c_uppercase_set']:
        return 'uppercase'
    if letter in settings['c_lowercase_set']:
        return 'lowercase'
    if letter in settings['c_numbers_set']:
        return 'numbers'
    return current_set

def input_string(string_ascii):
    track_letterlist = list(string_ascii)
    cur_set = 'uppercase' # default
    for letter in track_letterlist:
        if letter not in settings['c_complete']:
            letter = '?'
        distance_dict = find_distance(letter)
        dict_key = min(distance_dict, key=lambda k: abs(distance_dict[k]))
        enter_correct_set(dict_key, cur_set)
        # use sign on the modulo result to see if we are searching backward or forward
        push_button((lambda x: (x < 0 and 'Left' or 'Right'))(distance_dict[dict_key]), settings['t_press'], abs(distance_dict[dict_key]))
        push_button('Stop', settings['t_press'], 1)
        cur_set = return_current_set(letter, cur_set)
    push_button('Stop', settings['t_hold'], 1)

def enter_correct_set(wanted_set, current_set):
    times = settings['c_set_moves'][current_set][wanted_set]
    push_button('Pause', settings['t_press'], times)

def hw_push(timing, wiper):
    #SPI MAGIC
    command0 = 0b00000000 # CH0: 00h address + 00 write cmd + 00 data
    command1 = 0b00010000 # CH1: 01h address + 00 write cmd + 00 data
    spi.xfer([command0, wiper])
    spi.xfer([command1, wiper])
    GPIO.output(23, 1) # disable SHDN pin
    time.sleep(timing)
    GPIO.output(23, 0) # enable SHDN pin
    time.sleep(settings['t_press'])

def push_button(button, timing, times):
    for _ in range(times):
        # wiper values for each button from the config file
        hw_push(timing, int(settings['wipers'][button]))

def cleanup_exit():
    GPIO.cleanup()
    spi.close()
    print('Bye!')
    sys.exit()

def hardware_setup():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.OUT)
    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 976000
    return spi

def set_config(args):
    conf_file = args.conf
    try:
        with open(conf_file) as f:
            settings = yaml.safe_load(f)
    except (FileNotFoundError, IOError):
        print('No settings file found. Run configurator.py script first')
        raise

    return settings

def enter_labelling():
    push_button('Display', settings['t_hold'], 1)
    push_button('Stop', settings['t_press'], 2) # enter labelling mode


def manual_mode():
    print('> Connect your Sony Recorder and insert the MD you want to label')
    input('Press Enter when ready.')
    while True:
        print('Select the track you want to label on the recorder')
        input('Press Enter when ready.')
        enter_labelling()
        ascii_input = unidecode(input('Enter the name of the track:\n'))
        input_string(ascii_input)
        answer = input('Do you want to label another track? [Y/N]')
        if answer.casefold() != 'y':
            raise

def stdin_mode():
    for line in sys.stdin:
        enter_labelling()
        input_string(unidecode(line))
    raise

# actual program starts here

args = parse_arguments()

try:
    spi = hardware_setup()
    settings = set_config(args)

    if args.mode == 'hand':
        manual_mode()
    if args.mode == 'stdin':
        stdin_mode()

    print('> Connect your Sony Recorder and insert a blank MD')
    input('Press Enter when ready.')
    print('Wait for REC Standby...')
    push_button('Record', settings['t_press'], 1) # REC Standby
    time.sleep(1)

    print('> Open up Foobar2000 with the playlist you want to record')
    input('Press Enter when ready.')
    print('The following tracks will be burned & labelled:')
    playlist_info = request_playlist_info()
    tracklist = request_playlist_content(playlist_info)
    input('Press Enter to begin.')

    push_button('Pause', settings['t_press'], 1) # start recording
    set_mode_play(playlist_info)

    for track_number, track in enumerate(tracklist):
        try:
            if silent_track(track):
                print('Skipping labelling of a silent track')
                time.sleep(2.1)
            else:
                print(f'Recording: {tracklist[track_number]}')
                time.sleep(0.2)
                enter_labelling()
                input_string(tracklist[track_number])
                track_remaining = request_track_remaining()
                print(f'Track labelled. Time to TMark: {track_remaining:0.0f}s')
                time.sleep(track_remaining - settings['t_offset'])
                if track_number+1 != len(tracklist):
                    if not args.no_tmarks:
                        push_button('TMark', settings['t_press'], 1)
                else:
                    push_button('Stop', settings['t_press'], 1)

        except KeyboardInterrupt:
            answer = input('\nFinish recording current track? [Y/N] ')
            if answer.casefold() == 'y':
                track_remaining = request_track_remaining()
                print(f'Finishing track: {track}, time left: {track_remaining:0.0f}s')
                time.sleep(track_remaining)
                push_button('Stop', settings['t_press'], 1)
                set_stop()
                raise
            else:
                push_button('Stop', settings['t_press'], 1)
                set_stop()
                raise

    print('Waiting for TOC to save...')
    time.sleep(10)

finally:
    cleanup_exit()
