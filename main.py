from argparse import ArgumentParser, _SubParsersAction
from traceback import print_exc

from spotipy.exceptions import SpotifyException

from add_music import add_music
from download_music.spotify_dl import download_music
from terminal_utils import ERROR
from get_playlist_artists import get_playlist_artists

def add_music_subparser(subparsers: _SubParsersAction):
    parser: ArgumentParser = subparsers.add_parser('add_music')
    parser.add_argument('collection', help="spotify playlist/album id")
    parser.add_argument('--remove-saved', action='store_true')

def download_music_subparser(subparsers: _SubParsersAction):
    parser: ArgumentParser = subparsers.add_parser('download_music')
    parser.add_argument('--track', nargs=1, help="spotify track id")
    parser.add_argument('--playlist', nargs=1, help="spotify track id")

def get_playlist_artists_subparser(subparsers: _SubParsersAction):
    parser: ArgumentParser = subparsers.add_parser('get_playlist_artists')
    parser.add_argument('playlist', help="spotify playlist id")

def get_parser():
    parser = ArgumentParser(
        description='spotify-dl allows you to download your spotify songs')
    parser.add_argument('--verbose', action='store_true', help='verbose flag')
    parser.add_argument(
        '--traceback',
        action='store_true',
        help="enable traceback")
    subparsers = parser.add_subparsers(dest='subparser')
    add_music_subparser(subparsers)
    download_music_subparser(subparsers)
    get_playlist_artists_subparser(subparsers)
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    try:
        if args.subparser == 'add_music':
            add_music(args.collection, args.remove_saved)
        elif args.subparser == 'download_music':
            download_music(args)
        elif args.subparser == 'get_playlist_artists':
            get_playlist_artists(args.playlist)
        else:
            print(f'{ERROR} This is bad')
    except SpotifyException as err:
        print(f'{ERROR} {err}')
        if args.traceback:
            print_exc()
    except KeyboardInterrupt:
        print("Gracefully exiting")


if __name__ == "__main__":
    main()
