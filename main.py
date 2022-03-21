from argparse import ArgumentParser
from math import ceil
from typing import Iterable, List, Optional, TypeVar, TypedDict
from os import environ

from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyImplicitGrant
from tqdm import tqdm

PENDING_PLAYLIST = environ.get('SPOTIFY_PENDING_PLAYLIST', '0')
SCOPE = 'user-library-read playlist-modify-private playlist-modify-public'
auth_manager = SpotifyImplicitGrant(redirect_uri='localhost:8080', scope=SCOPE)
cache_token = auth_manager.get_access_token()
spotify = Spotify(cache_token)

T = TypeVar('T')

class Track(TypedDict):
    id: Optional[str]

class Item(TypedDict):
    track: Optional[Track]

def get_playlist_id() -> str:
    parser = ArgumentParser(description='spotify-dl allows you to download your spotify songs')
    parser.add_argument('--playlist', nargs=1, help="spotify track id", required=True)
    args = parser.parse_args()
    return args.playlist[0]

def get_playlist_items(playlist_id: str):
    response = spotify.playlist_items(playlist_id)
    if response is None:
        return []
    items, total = response['items'], response['total']
    while len(items) < total:
        response = spotify.playlist_items(playlist_id, offset=len(items))
        if response is None:
            return items
        items += response['items']
    return items

def id_is_safe(item: Optional[Item]):
    if item is None:
        return False
    track = item['track']
    if track is None:
        return False
    return track['id'] is not None

def get_tracks_ids(playlist_id: str):
    items = get_playlist_items(playlist_id)
    return [item['track']['id'] for item in tqdm(items, 'Getting playlist tracks') if id_is_safe(item)]

def create_chunks(arr: List[T], chunk_size: int) -> Iterable[List[T]]:
    number_of_chunks = ceil(len(arr) / chunk_size)
    for chunk in range(number_of_chunks):
        start = chunk * chunk_size
        end = start + chunk_size
        yield arr[start:end]

def remove_saved(ids: List[str]):
    saved_ids: List[bool] = []
    for chunk in create_chunks(ids, 50):
        response = spotify.current_user_saved_tracks_contains(chunk)
        saved_ids += [True] * 50 if response is None else response
    if len(saved_ids) != len(ids):
        print(len(saved_ids), len(ids))
        assert False, "There must be the same amount of elements for the filter to work"
    return [id for idx, id in enumerate(ids) if not saved_ids[idx]]

def add_songs(ids: List[str]):
    for chunk in create_chunks(ids, 100):
        try:
            spotify.playlist_add_items(PENDING_PLAYLIST, chunk)
        except SpotifyException as err:
            print(err)

def main():
    playlist_id = get_playlist_id()
    ids = get_tracks_ids(playlist_id)
    unsaved_ids = remove_saved(ids)
    add_songs(unsaved_ids)

if __name__ == "__main__":
    main()
