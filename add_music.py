from typing import List, Optional, Set, TypedDict, Callable
from os import environ

from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyImplicitGrant
from tqdm import tqdm

from utils import create_chunks

PENDING_PLAYLIST = environ.get('SPOTIFY_PENDING_PLAYLIST', '0')
SCOPE = 'user-library-read playlist-modify-private playlist-modify-public'
auth_manager = SpotifyImplicitGrant(redirect_uri='http://localhost:8080', scope=SCOPE)
cache_token = auth_manager.get_access_token()
spotify = Spotify(cache_token)

class Track(TypedDict):
    id: Optional[str]

class Item(TypedDict):
    id: str
    track: Optional[Track]

class SpotifyResponse(TypedDict):
    next: Optional[bool]
    items: List[Item]

def get_all_items(response: Optional[SpotifyResponse]):
    assert response is not None, "Problem with getting playlist items"
    items = response['items']
    while response['next']:
        response = spotify.next(response)
        assert response is not None, "Problem with getting items"
        items += response['items']
    return items

def get_playlist_tracks(playlist_id: str):
    response = spotify.playlist_items(playlist_id)
    items = get_all_items(response)
    return [item['track'] for item in items if item['track'] is not None]

def get_album_tracks(album_id: str):
    response = spotify.album_tracks(album_id)
    return get_all_items(response)

def id_is_safe(track: Optional[Track]):
    if track is None:
        return False
    return track['id'] is not None

def get_tracks_ids(
    collection_id: str,
    acceptable: Callable[[Optional[Track]], bool] = id_is_safe
) -> List[str]:
    print(f"Gettings tracks of {collection_id}")
    if "playlist" in collection_id:
        tracks = get_playlist_tracks(collection_id)
    elif "album" in collection_id:
        tracks = get_album_tracks(collection_id)
    else:
        tracks = get_playlist_tracks(collection_id)
    return [
        track['id']
        for track in tqdm(tracks, 'Getting playlist tracks')
        if acceptable(track) and track['id'] is not None
    ]

def non_duplicate_collection_tracks(collection_id: str, playlist_ids: Set[str]):
    def acceptable(track: Optional[Track]):
        if track is None:
            return False
        return id_is_safe(track) and track['id'] not in playlist_ids
    return get_tracks_ids(collection_id, acceptable)

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
    print(f"Adding {len(ids)} songs")
    for chunk in create_chunks(ids, 100):
        try:
            spotify.playlist_add_items(PENDING_PLAYLIST, chunk)
        except SpotifyException as err:
            print(err)

def remove_songs(ids: List[str], playlist_id: str):
    print(f"Removing {len(ids)} songs")
    for chunk in create_chunks(ids, 100):
        try:
            spotify.playlist_remove_all_occurrences_of_items(playlist_id, chunk)
        except SpotifyException as err:
            print(err)

def remove_saved_songs_of_pending_playlist(ids: List[str]):
    print("Removing saved songs")
    saved_ids = filter_by_saved(ids, get_saved=True)
    remove_songs(saved_ids, PENDING_PLAYLIST)
    print("Removed saved songs")

def add_music(collection_id: str, remove_saved: bool):
    playlist_ids = get_tracks_ids(PENDING_PLAYLIST)
    if remove_saved:
        remove_saved_songs_of_pending_playlist(playlist_ids)
    ids = non_duplicate_collection_tracks(collection_id, set(playlist_ids))
    unsaved_ids = filter_by_saved(ids)
    add_songs_to_pending_playlist(unsaved_ids)
