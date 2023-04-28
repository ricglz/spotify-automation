import re
from typing import Iterable, List, Optional, TypedDict, TypeVar

from spotipy import Spotify
from spotipy.exceptions import SpotifyException
from spotipy.oauth2 import SpotifyImplicitGrant

from utils import create_chunks

T = TypeVar('T')

SCOPE = 'user-library-read playlist-modify-private playlist-modify-public'
auth_manager = SpotifyImplicitGrant(
    redirect_uri='http://localhost:8080',
    scope=SCOPE,
)
cache_token = auth_manager.get_access_token()
spotify = Spotify(cache_token)


class WithId(TypedDict):
    id: str
class Album(TypedDict):
    '''Type for an album'''
    name: str
class Artist(WithId, TypedDict):
    '''Type for an artist'''
    name: str
    genres: List[str]
class SimplifiedArtist(WithId, TypedDict):
    '''Type for an artist'''
    name: str
class Track(WithId, TypedDict):
    '''Type for a track'''
    album: Album
    artists: List[SimplifiedArtist]
    id: str
    name: str
class Item(WithId, TypedDict):
    id: str
    track: Optional[Track]

class GetPlaylistTracksResponse(TypedDict):
    next: Optional[bool]
    items: List[Item]

def get_all_items(response: Optional[GetPlaylistTracksResponse]):
    assert response is not None, "Problem with getting playlist items"
    for item in response['items']:
        yield item
    while response['next']:
        response = spotify.next(response)
        assert response is not None, "Problem with getting items"
        for item in response['items']:
            yield item

def get_playlist_tracks(playlist_id: str):
    response = spotify.playlist_items(playlist_id)
    for item in get_all_items(response):
        track = item["track"]
        if track is not None:
            yield track

def flatten(iterator: Iterable[Iterable[T]]) -> Iterable[T]:
    for list in iterator:
        for element in list:
            yield element

def get_playlist_artists(playlist_id: str):
    tracks = get_playlist_tracks(playlist_id)
    return flatten(
        track["artists"]
        for track in tracks
        if track is not None and track["artists"] is not None)

def get_unique_artists_names(artists: Iterable[SimplifiedArtist]):
    return set(artist["name"] for artist in artists)

def get_playlist_artists_names(playlist_id: str):
    return get_unique_artists_names(get_playlist_artists(playlist_id))

def artist_is_playlist(simplified_artist: SimplifiedArtist):
    artist: Optional[Artist] = spotify.artist(simplified_artist["id"])
    if artist is None:
        return False
    return any(
        re.search(r"(latin|mexican)", genre) is not None
        for genre in artist["genres"]
    )

def get_playlist_latin_artists_names(playlist_id: str):
    artists = get_playlist_artists(playlist_id)
    return get_unique_artists_names(
        artist for artist in artists if artist_is_playlist(artist)
    )

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
        # TODO: Throw exception
        raise Exception()
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
            spotify.playlist_remove_all_occurrences_of_items(
                playlist_id,
                chunk
            )
        except SpotifyException as err:
            print(err)

def get_track(track_id: str) -> Optional[Track]:
    return spotify.track(track_id)
