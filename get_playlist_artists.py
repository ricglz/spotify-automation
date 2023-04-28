from spotify import get_playlist_latin_artists_names


def get_playlist_artists(playlist_id: str):
    names = get_playlist_latin_artists_names(playlist_id)
    with open("artists.txt", "w") as f:
        f.writelines(f"{name}\n" for name in names)
