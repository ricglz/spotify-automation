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
    assert response is not None, "Problem with getting playlist items"
    items = response['items']
    while response['next']:
        response = spotify.next(response)
        assert response is not None, "Problem with getting playlist items"
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

def get_saved_ids(ids: List[str]):
    saved_ids: List[bool] = []
    for chunk in create_chunks(ids, 50):
        response = spotify.current_user_saved_tracks_contains(chunk)
        saved_ids += [True] * 50 if response is None else response
    if len(saved_ids) != len(ids):
        print(len(saved_ids), len(ids))
        assert False, "There must be the same amount of elements for the filter to work"
    return saved_ids

def filter_by_saved(ids: List[str], get_saved = False):
    saved_ids = get_saved_ids(ids)
    return [ids[idx] for idx, saved in enumerate(saved_ids) if (saved if get_saved else not saved)]

def add_songs_to_pending_playlist(ids: List[str]):
    for chunk in create_chunks(ids, 100):
        try:
            spotify.playlist_add_items(PENDING_PLAYLIST, chunk)
        except SpotifyException as err:
            print(err)

def remove_songs(ids: List[str], playlist_id: str):
    for chunk in create_chunks(ids, 100):
        try:
            spotify.playlist_remove_all_occurrences_of_items(playlist_id, chunk)
        except SpotifyException as err:
            print(err)

def remove_saved_songs_of_pending_playlist():
    ids = get_tracks_ids(PENDING_PLAYLIST)
    saved_ids = filter_by_saved(ids, get_saved=True)
    remove_songs(saved_ids, PENDING_PLAYLIST)

def main():
    remove_saved_songs_of_pending_playlist()
    playlist_id = get_playlist_id()
    ids = get_tracks_ids(playlist_id)
    unsaved_ids = filter_by_saved(ids)
    add_songs_to_pending_playlist(unsaved_ids)

if __name__ == "__main__":
    main()
