from argparse import ArgumentParser

from spotipy import Spotify, SpotifyException
from spotipy.oauth2 import SpotifyClientCredentials
from tqdm import tqdm

spotify = Spotify(client_credentials_manager=SpotifyClientCredentials())

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

def get_tracks(playlist_id: str):
    items = get_playlist_items(playlist_id)
    return [item['track'] for item in tqdm(items, 'Getting playlist tracks')]

def get_playlist_id() -> str:
    parser = ArgumentParser(description='spotify-dl allows you to download your spotify songs')
    parser.add_argument('--playlist', nargs=1, help="spotify track id", required=True)
    args = parser.parse_args()
    return args.playlist[0]

def main():
    playlist_id = get_playlist_id()
    tracks = get_tracks(playlist_id)
    print(playlist_id, tracks)

if __name__ == "__main__":
    main()
