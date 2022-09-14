from argparse import ArgumentParser, _SubParsersAction

from add_music import add_music

def add_music_subparser(subparsers: _SubParsersAction):
    parser = subparsers.add_parser('add_music')
    parser.add_argument('--collection', nargs=1, help="spotify playlist/album id", required=True)
    parser.add_argument('--remove-saved', action='store_true')

def get_parser():
    parser = ArgumentParser(description='spotify-dl allows you to download your spotify songs')
    subparsers = parser.add_subparsers(dest='subparser')
    add_music_subparser(subparsers)
    return parser

def main():
    parser = get_parser()
    args = parser.parse_args()
    if args.subparser == 'add_music':
        add_music(args.collection[0], args.remove_saved)
    else:
        print('This is bad')

if __name__ == "__main__":
    main()
