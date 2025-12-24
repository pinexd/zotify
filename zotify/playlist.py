from zotify.const import ITEMS, ID, TRACK, NAME
from zotify.termoutput import Printer
from zotify.track import download_track
from zotify.utils import split_input
from zotify.zotify import Zotify
import time

MY_PLAYLISTS_URL = 'https://api.spotify.com/v1/me/playlists'
PLAYLISTS_URL = 'https://api.spotify.com/v1/playlists'


def get_all_playlists():
    """ Returns list of users playlists """
    playlists = []
    limit = 50
    offset = 0

    while True:
        resp = Zotify.invoke_url_with_params(MY_PLAYLISTS_URL, limit=limit, offset=offset)
        offset += limit
        playlists.extend(resp[ITEMS])
        if len(resp[ITEMS]) < limit:
            break

    return playlists


def get_playlist_songs(playlist_id):
    """ returns list of songs in a playlist """
    songs = []
    offset = 0
    limit = 100
    while True:
        resp = Zotify.invoke_url_with_params(
            f'{PLAYLISTS_URL}/{playlist_id}/tracks',
            limit=limit,
            offset=offset,
            market='from_token'  # Optional: helps with track availability
        )
        if 'error' in resp:
            if resp['error'].get('status') == 429:
                retry_after = int(resp['error'].get('headers', {}).get('Retry-After', 5))  # Fallback to 5s if missing
                Printer.print(PrintChannel.WARNINGS, f"Rate limit hit (429). Waiting {retry_after} seconds...")
                time.sleep(retry_after + 1)  # Add 1s buffer
                continue  # Retry the same page
            raise ValueError(f"Spotify API error: {resp['error'].get('message', 'Unknown error')} (status: {resp['error'].get('status', 'N/A')})")
        songs.extend(resp[ITEMS])
        if len(resp[ITEMS]) < limit:
            break
        offset += limit
        time.sleep(2)
    return songs


def get_playlist_info(playlist_id):
    """ Returns information scraped from playlist """
    (raw, resp) = Zotify.invoke_url(f'{PLAYLISTS_URL}/{playlist_id}?fields=name,owner(display_name)&market=from_token')
    return resp['name'].strip(), resp['owner']['display_name'].strip()


def download_playlist(playlist):
    """Downloads all the songs from a playlist"""

    playlist_songs = [song for song in get_playlist_songs(playlist[ID]) if song[TRACK] is not None and song[TRACK][ID]]
    p_bar = Printer.progress(playlist_songs, unit='song', total=len(playlist_songs), unit_scale=True)
    enum = 1
    for song in p_bar:
        download_track('extplaylist', song[TRACK][ID], extra_keys={'playlist': playlist[NAME], 'playlist_num': str(enum).zfill(2)}, disable_progressbar=True)
        p_bar.set_description(song[TRACK][NAME])
        enum += 1


def download_from_user_playlist():
    """ Select which playlist(s) to download """
    playlists = get_all_playlists()

    count = 1
    for playlist in playlists:
        print(str(count) + ': ' + playlist[NAME].strip())
        count += 1

    selection = ''
    print('\n> SELECT A PLAYLIST BY ID')
    print('> SELECT A RANGE BY ADDING A DASH BETWEEN BOTH ID\'s')
    print('> OR PARTICULAR OPTIONS BY ADDING A COMMA BETWEEN ID\'s\n')
    while len(selection) == 0:
        selection = str(input('ID(s): '))
    playlist_choices = map(int, split_input(selection))

    for playlist_number in playlist_choices:
        playlist = playlists[playlist_number - 1]
        print(f'Downloading {playlist[NAME].strip()}')
        download_playlist(playlist)

    print('\n**All playlists have been downloaded**\n')
