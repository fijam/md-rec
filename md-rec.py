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
    return parser.parse_args()

def request_playlist_info():
    response = requests.get(server_url + '/api/playlists')
    # return a tuple of playlist ID and number of tracks
    return response.json()['playlists'][0]['id'], response.json()['playlists'][0]['itemCount']

def request_playlist_content(playlist_tuple):
    t_list = []
    total_time = 0
    item_count = playlist_tuple[1]
    payload = {'playlists':'true', 'playlistItems':'true',
               'plref':playlist_tuple[0], 'plrange':'0:'+str(item_count),
               'plcolumns':'%artist% - %title%, %length_seconds%'}
    response = requests.get(server_url+'/api/query', params=payload)

    for i in range(item_count):
        ascii_track_name = unidecode(response.json()['playlistItems']['items'][i]['columns'][0])
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
    response = requests.get(server_url + '/api/player')
    remaining = (response.json()['player']['activeItem']['duration']
                 - response.json()['player']['activeItem']['position'])
    # return remaining time in track (in seconds)
    return remaining

def set_mode_play(playlist_tuple):
    requests.post(server_url + '/api/player', params={'isMuted':'false', 'playbackMode':'0'})
    requests.post(server_url + '/api/player/play/' + playlist_tuple[0]+'/0')

def set_stop():
    requests.post(server_url + '/api/player/stop')

def calc_midpoint(char_set):
    return (len(char_set)+len(common_set)) //2

def calc_index(char_set, half, letter):
    midpoint = calc_midpoint(char_set)
    if half == 'bottom':
        return char_set[:midpoint].index(letter)
    if half == 'top':
        return list(reversed(char_set[midpoint:])).index(letter)+len(common_set)+1
    if half == 'common': #do not halve
        return list(reversed(char_set)).index(letter)+1
    return None

def input_string(string_ascii):
    track_letterlist = list(string_ascii)
    cur_set = 'uppercase' # default

    for letter in track_letterlist:
        if letter in common_set:
            input_ltr(cur_set, cur_set, calc_index(common_set, 'common', letter), 'Left')
            cur_set = cur_set
        elif letter in uppercase_set[:calc_midpoint(uppercase_set)]:
            input_ltr('uppercase', cur_set, calc_index(uppercase_set, 'bottom', letter), 'Right')
            cur_set = 'uppercase'
        elif letter in uppercase_set[calc_midpoint(uppercase_set):]:
            input_ltr('lowercase', cur_set, calc_index(uppercase_set, 'top', letter), 'Left')
            cur_set = 'uppercase'
        elif letter in lowercase_set[:calc_midpoint(lowercase_set)]:
            input_ltr('lowercase', cur_set, calc_index(lowercase_set, 'bottom', letter), 'Right')
            cur_set = 'lowercase'
        elif letter in lowercase_set[calc_midpoint(lowercase_set):]:
            input_ltr('numbers', cur_set, calc_index(lowercase_set, 'top', letter), 'Left')
            cur_set = 'lowercase'
        elif letter in numbers_set[:calc_midpoint(numbers_set)]:
            input_ltr('numbers', cur_set, calc_index(numbers_set, 'bottom', letter), 'Right')
            cur_set = 'numbers'
        elif letter in numbers_set[calc_midpoint(numbers_set):]:
            input_ltr('uppercase', cur_set, calc_index(numbers_set, 'top', letter), 'Left')
            cur_set = 'numbers'
        else:
            input_ltr('uppercase', cur_set, 11, 'Left') # catch-all replace with '?'
            cur_set = 'numbers'

    push_button('Stop', hold, 1)

def input_ltr(wanted_set, current_set, letter_index, search_button):
    times = set_moves[current_set][wanted_set]
    push_button('Pause', press, times)
    push_button(search_button, press, letter_index)
    push_button('Stop', press, 1)

def hw_push(timing, wiper):
    #SPI MAGIC
    command0 = 0b00000000 # CH0: 00h address + 00 write cmd + 00 data
    command1 = 0b00010000 # CH1: 01h address + 00 write cmd + 00 data
    spi.xfer([command0, wiper])
    spi.xfer([command1, wiper])
    GPIO.output(23, 1) # disable SHDN pin
    time.sleep(timing)
    GPIO.output(23, 0) # enable SHDN pin
    time.sleep(press)

def push_button(button, timing, times):
    for _ in range(times):
        # wiper values for each button from the config file
        hw_push(timing, int(wiper_dict[button]))

def cleanup_exit():
    push_button('Stop', press, 1)
    set_stop()
    GPIO.cleanup()
    print('Bye!')
    sys.exit(0)

if __name__ == "__main__":

    # parse arguments
    args = parse_arguments()

    # configuration
    conf_file = args.conf
    try:
        with open(conf_file) as f:
            settings = yaml.safe_load(f)
    except (FileNotFoundError, IOError):
        print('No settings file found. Run configurator.py script first')
        sys.exit(1)

    server_url = settings['server_url']
    offset = settings['timing_offset']
    press = settings['timing_press']
    hold = settings['timing_hold']
    wiper_dict = settings['wipers']
    set_moves = settings['char_set_moves']
    common_set = settings['char_common_set']
    lowercase_set = settings['char_lowercase_set']
    uppercase_set = settings['char_uppercase_set']
    numbers_set = settings['char_numbers_set']
    #unsupported_set = ['[', '\', ']', '^', '{', '|', '}', '~']

    # hardware setup
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(23, GPIO.OUT)

    spi = spidev.SpiDev()
    spi.open(0, 0)
    spi.max_speed_hz = 976000

    # actual program starts here

    print('> Connect your Sony Recorder and insert a blank MD')
    input('Press Enter when ready.')
    print('Wait for REC Standby...')
    push_button('Record', press, 1) # REC Standby
    time.sleep(1)

    print('> Open up Foobar2000 with the playlist you want to record')
    input('Press Enter when ready.')
    print('The following tracks will be burned & labelled:')
    playlist_info = request_playlist_info()
    tracklist = request_playlist_content(playlist_info)
    input('Press Enter to begin.')

    push_button('Pause', press, 1) # start recording
    set_mode_play(playlist_info)

    for track_number, track in enumerate(tracklist):
        try:
            print(f'Recording: {tracklist[track_number]}')
            time.sleep(0.2)
            push_button('Display', hold, 1)
            push_button('Stop', press, 2) # enter labelling mode
            input_string(tracklist[track_number])
            track_remaining = request_track_remaining()
            print(f'Track labelled. Time to TMark: {track_remaining:0.0f}s')
            time.sleep(track_remaining - offset)
            if track_number+1 != len(tracklist):
                push_button('TMark', press, 1)
            else:
                push_button('Stop', press, 1)

        except KeyboardInterrupt:
            answer = input('\nFinish recording current track? [Y/N] ')
            if answer == 'Y':
                track_remaining = request_track_remaining()
                print(f'Finishing track: {track}, time left: {track_remaining:0.0f}s')
                time.sleep(track_remaining - offset)
                cleanup_exit()
            else:
                cleanup_exit()

    print('Waiting for TOC to save...')
    time.sleep(10)
    cleanup_exit()
