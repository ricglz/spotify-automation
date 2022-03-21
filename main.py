from argparse import ArgumentParser
from math import ceil
from typing import List

from spotipy import Spotify
from spotipy.oauth2 import SpotifyOAuth
from tqdm import tqdm

auth_manager = SpotifyOAuth(redirect_uri='localhost:8080')
cache_token = auth_manager.get_access_token(as_dict=False)
spotify = Spotify(cache_token)

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

def get_tracks_ids(playlist_id: str):
    items = get_playlist_items(playlist_id)
    return [item['track']['id'] for item in tqdm(items, 'Getting playlist tracks')]

def get_playlist_id() -> str:
    parser = ArgumentParser(description='spotify-dl allows you to download your spotify songs')
    parser.add_argument('--playlist', nargs=1, help="spotify track id", required=True)
    args = parser.parse_args()
    return args.playlist[0]

def remove_saved(ids: List[str]):
    chunks = ceil(len(ids) / 50)
    saved_ids: List[bool] = []
    for chunk in range(chunks):
        start = chunk
        end = chunk + 50
        response = spotify.current_user_saved_tracks_contains(ids[start:end])
        saved_ids += [True] * 50 if response is None else response
    assert len(saved_ids) == len(ids), "There must be the same amount of elements for the filter to work"
    return [id for idx, id in enumerate(ids) if not saved_ids[idx]]

def main():
    playlist_id = get_playlist_id()
    ids = get_tracks_ids(playlist_id)
    unsaved_ids = remove_saved(ids)
    print(len(ids), len(unsaved_ids))

if __name__ == "__main__":
    main()
