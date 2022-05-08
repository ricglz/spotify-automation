from argparse import ArgumentParser
from math import ceil
from typing import Any, Iterable, List, Optional, Tuple, TypeVar, TypedDict
from os import environ

from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyImplicitGrant
from tqdm import tqdm

PENDING_PLAYLIST = environ.get('SPOTIFY_PENDING_PLAYLIST', '0')
SCOPE = 'user-library-read playlist-modify-private playlist-modify-public'
auth_manager = SpotifyImplicitGrant(redirect_uri='http://localhost:8080', scope=SCOPE)
cache_token = auth_manager.get_access_token()
spotify = Spotify(cache_token)

T = TypeVar('T')

class Track(TypedDict):
    id: Optional[str]

class Item(TypedDict):
    track: Optional[Track]

def get_collection_id() -> Tuple[str, bool]:
    parser = ArgumentParser(description='spotify-dl allows you to download your spotify songs')
    parser.add_argument('--collection', nargs=1, help="spotify playlist/album id", required=True)
    parser.add_argument('--remove-saved', action='store_true')
    args = parser.parse_args()
    return (args.collection[0], args.remove_saved)

def get_all_items(response: Any):
    items = response['items']
    while response['next']:
        response = spotify.next(response)
        assert response is not None, "Problem with getting items"
        items += response['items']
    return items

def get_playlist_tracks(playlist_id: str):
    response = spotify.playlist_items(playlist_id)
    assert response is not None, "Problem with getting playlist items"
    items = get_all_items(response)
    return [item['track'] for item in items if item['track'] is not None]

def get_album_tracks(album_id: str):
    response = spotify.album_tracks(album_id)
    assert response is not None, "Problem with getting album items"
    return get_all_items(response)

def id_is_safe(track: Optional[Track]):
    if track is None:
        return False
    return track['id'] is not None

def get_tracks_ids(collection_id: str):
    if "playlist" in collection_id:
        tracks = get_playlist_tracks(collection_id)
    elif "album" in collection_id:
        tracks = get_album_tracks(collection_id)
    else:
        tracks = get_playlist_tracks(collection_id)
    return [track['id'] for track in tqdm(tracks, 'Getting playlist tracks') if id_is_safe(track)]

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
    print("Removing saved songs")
    ids = get_tracks_ids(PENDING_PLAYLIST)
    saved_ids = filter_by_saved(ids, get_saved=True)
    remove_songs(saved_ids, PENDING_PLAYLIST)
    print("Removed saved songs")

def main():
    collection_id, remove_saved = get_collection_id()
    if remove_saved:
        remove_saved_songs_of_pending_playlist()
    ids = get_tracks_ids(collection_id)
    unsaved_ids = filter_by_saved(ids)
    add_songs_to_pending_playlist(unsaved_ids)

if __name__ == "__main__":
    main()
