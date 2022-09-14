from typing import List, Optional, TypedDict

from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyImplicitGrant

from utils import create_chunks

SCOPE = 'user-library-read playlist-modify-private playlist-modify-public'
auth_manager = SpotifyImplicitGrant(redirect_uri='http://localhost:8080', scope=SCOPE)
cache_token = auth_manager.get_access_token()
spotify = Spotify(cache_token)

class WithId(TypedDict):
    id: str
class Album(TypedDict):
    '''Type for an artist'''
    name: str
class Artist(TypedDict):
    '''Type for an artist'''
    name: str
class Track(WithId, TypedDict):
    '''Type for a track'''
    album: Album
    artists: List[Artist]
    id: str
    name: str
class Item(WithId, TypedDict):
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

def get_tracks(collection_id: str):
    if "playlist" in collection_id:
        return get_playlist_tracks(collection_id)
    if "album" in collection_id:
        return get_album_tracks(collection_id)
    return get_playlist_tracks(collection_id)

def get_saved_ids(ids: List[str]):
    saved_ids: List[bool] = []
    for chunk in create_chunks(ids, 50):
        response = spotify.current_user_saved_tracks_contains(chunk)
        saved_ids += [True] * 50 if response is None else response
    if len(saved_ids) != len(ids):
        print(len(saved_ids), len(ids))
        assert False, "There must be the same amount of elements for the filter to work"
    return saved_ids

def add_songs_to_playlist(ids: List[str], playlist_id: str):
    print(f"Adding {len(ids)} songs")
    for chunk in create_chunks(ids, 100):
        try:
            spotify.playlist_add_items(playlist_id, chunk)
        except SpotifyException as err:
            print(err)

def remove_songs_from_playlist(ids: List[str], playlist_id: str):
    print(f"Removing {len(ids)} songs")
    for chunk in create_chunks(ids, 100):
        try:
            spotify.playlist_remove_all_occurrences_of_items(playlist_id, chunk)
        except SpotifyException as err:
            print(err)

def get_track(track_id: str) -> Optional[Track]:
    return spotify.track(track_id)
