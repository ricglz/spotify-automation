from typing import List, Optional, Set, Callable, TypeGuard
from os import environ

from tqdm import tqdm

from spotify import WithId, add_songs_to_playlist, get_saved_ids, \
                    get_tracks, remove_songs_from_playlist

PENDING_PLAYLIST = environ.get('SPOTIFY_PENDING_PLAYLIST', '0')

def id_is_safe(track: Optional[WithId]) -> TypeGuard[WithId]:
    if track is None:
        return False
    return track['id'] is not None

def get_tracks_ids(
    collection_id: str,
    acceptable: Callable[[Optional[WithId]], TypeGuard[WithId]] = id_is_safe
):
    print(f"Gettings tracks of {collection_id}")
    tracks = get_tracks(collection_id)
    return [
        track['id']
        for track in tqdm(tracks, 'Getting playlist tracks')
        if acceptable(track) and track['id'] is not None
    ]

def non_duplicate_collection_tracks(
    collection_id: str,
    playlist_ids: Set[str],
):
    def acceptable(track: Optional[WithId]) -> TypeGuard[WithId]:
        if track is None:
            return False
        return id_is_safe(track) and track['id'] not in playlist_ids
    return get_tracks_ids(collection_id, acceptable)

def filter_by_saved(ids: List[str], get_saved=False):
    saved_ids = get_saved_ids(ids)
    return [
        ids[idx]
        for idx, saved in enumerate(saved_ids)
        if saved != get_saved
    ]

def add_songs_to_pending_playlist(ids: List[str]):
    add_songs_to_playlist(ids, PENDING_PLAYLIST)

def remove_saved_songs_of_pending_playlist(ids: List[str]):
    print("Removing saved songs")
    saved_ids = filter_by_saved(ids, get_saved=True)
    remove_songs_from_playlist(saved_ids, PENDING_PLAYLIST)
    print("Removed saved songs")

def add_music(collection_id: str, remove_saved: bool):
    playlist_ids = get_tracks_ids(PENDING_PLAYLIST)
    if remove_saved:
        remove_saved_songs_of_pending_playlist(playlist_ids)
    ids = non_duplicate_collection_tracks(collection_id, set(playlist_ids))
    unsaved_ids = filter_by_saved(ids)
    add_songs_to_pending_playlist(unsaved_ids)
