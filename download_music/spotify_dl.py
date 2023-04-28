#!/usr/local/bin/python3
"""
spotify_dl.py

Downloads music from spotify using youtube as an intermidiate
"""

from argparse import Namespace
from concurrent.futures import ThreadPoolExecutor
from os import environ, remove, path
from subprocess import run
from typing import Iterable, Optional, TextIO, Tuple, List, TypedDict
from io import open

from tqdm import tqdm
from ytmusicapi import YTMusic

from spotify import get_playlist_tracks, get_track
from download_music.storage import Storage
from terminal_utils import ACTION, ERROR

# =======================
#   Youtube application
# =======================
yt_music = YTMusic()

# =======================
#   Other constants
# =======================
storage: Optional[Storage] = None

# =======================
#   Types
# =======================
TrackInfo = Tuple[str, str, str]
class Album(TypedDict):
    '''Type for an artist'''
    name: str
class Artist(TypedDict):
    '''Type for an artist'''
    name: str
class Track(TypedDict):
    '''Type for a track'''
    album: Album
    artists: List[Artist]
    id: str
    name: str
class Item(TypedDict):
    '''Type for a track'''
    track: Track

# =======================
#   Actual code
# =======================
def get_tracks(args: Namespace):
    '''Gets a list of tracks based if is a single track or a list of them'''
    if args.track:
        track = get_track(args.track[0])
        return None if track is None else [track]
    if args.playlist:
        return get_playlist_tracks(args.playlist[0])
    return None


def scrap_youtube_link(query: str) -> str:
    """Scrap youtube content to search for the first link"""
    try:
        response = yt_music.search(query, filter='songs', limit=1)[0]
    except IndexError:
        tqdm.write(f'Could not found {query}')
        return ''
    video_id: str = response['videoId']
    video_link = f'http://youtube.com/watch?v={video_id}'
    return video_link

def get_track_info(track: Track) -> TrackInfo:
    """Gets the track name using its track id"""
    artist_name = track['artists'][0]['name']
    album_name = track['album']['name']
    track_name = track['name']
    return track_name, artist_name, album_name

def get_youtube_link(track: Track):
    """
    Gets the youtube link either by scrapping the results site
    or by using the google api
    """
    track_info = get_track_info(track)
    query = ' '.join(track_info)
    return scrap_youtube_link(query)

def get_link(track: Track) -> str:
    '''Gets the link of a track'''
    assert storage is not None
    try:
        link = storage.get_link(track['id'])
    except KeyError:
        link = get_youtube_link(track)
        if link != '':
            storage.store_link(track['id'], link)
    return link

def get_links(tracks: List[Track]):
    '''Gets the links of the tracks'''
    with ThreadPoolExecutor() as executor:
        pool_iterator = tqdm(
            executor.map(get_link, tracks),
            desc='Getting links',
            total=len(tracks),
        )
    return set(filter(lambda x: x != '', pool_iterator))

def download_youtube(batch_filename: str):
    """Downloading the track"""
    print(f'{ACTION} downloading song...')
    run(['add_music', '--batch-file', batch_filename], check=False)

def write_links_in_file(file: TextIO, links: Iterable[str]):
    for link in tqdm(links, desc='Writting file'):
        file.write(f'{link}\n')

def handle_links_in_tmp_file(links: Iterable[str]):
    filename = path.expanduser("~/Music/legal/temp.txt")
    with open(filename, 'w', encoding='utf-8') as file:
        write_links_in_file(file, links)
    download_youtube(filename)
    remove(filename)

def download_music(args: Namespace):
    """Main process"""
    global storage

    storage = Storage(environ.get('SPOTIFY_DATABASE', ''))
    tracks = get_tracks(args)
    if tracks is None:
        print(f'{ERROR} use --help for help')
        return
    links = get_links(list(tracks))
    handle_links_in_tmp_file(links)
