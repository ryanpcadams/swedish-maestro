import yt_dlp
from mutagen.id3 import ID3, APIC, COMM
from mutagen.mp3 import MP3
from mutagen.easyid3 import EasyID3
import requests
import json
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials, SpotifyOAuth
import os
import datetime

os.environ["SPOTIPY_CLIENT_ID"] = "0124eb5e28344b1994d6e7fece490afa"
os.environ["SPOTIPY_CLIENT_SECRET"] = "399537abb2be43cea872fd07eeee2306"
os.environ["SPOTIPY_REDIRECT_URI"] = "https://localhost:8888/callback"

sp = spotipy.Spotify(
    auth_manager=SpotifyOAuth(
        client_id=os.environ["SPOTIPY_CLIENT_ID"],
        client_secret=os.environ["SPOTIPY_CLIENT_SECRET"],
        redirect_uri=os.environ["SPOTIPY_REDIRECT_URI"],
        scope="user-library-read",
    )
)


def track_length(milliseconds):
    length = ""
    seconds = milliseconds // 1000
    minutes = seconds // 60
    hours = minutes // 60
    if hours:
        length = f"{hours}:"
    return f"{length}{minutes%60}:{seconds%60}"


config = {"tracks": {}, "artwork": {}}
error_codes = {}


def download_track(track_id, output_dir=os.getcwd()):
    resp = sp.track(track_id)
    track_config = {}
    track_config["metadata"] = {
        "title": resp["name"],
        "artist": "; ".join([artist["name"] for artist in resp["artists"]]),
        "album": resp["album"]["name"],
        "albumartist": "; ".join(
            [artist["name"] for artist in resp["album"]["artists"]]
        ),
        "length": track_length(resp["duration_ms"]),
        "date": resp["album"]["release_date"],
        "discnumber": str(resp["disc_number"]),
        "tracknumber": str(resp["track_number"]),
    }

    track_config[
        "file"
    ] = f"{output_dir}\\{''.join(e for e in track_config['metadata']['title'] if e.isalnum())}.mp3"
    track_config["artwork_url"] = sorted(
        resp["album"]["images"], key=lambda i: i["height"], reverse=True
    )[0]["url"]

    print(
        f"{track_config['metadata']['title']} {track_config['artwork_url'] in config['artwork']}"
    )

    if track_config["artwork_url"] not in config["artwork"]:
        config["artwork"][track_config["artwork_url"]] = requests.get(
            track_config["artwork_url"]
        ).content

    with yt_dlp.YoutubeDL({"noplaylist": True}) as ydl:
        search_url = (
            "ytsearch1:"
            + f"{track_config['metadata']['artist'].split(';')[0]} "
            + f"{track_config['metadata']['title']} "
            + '"Auto-generated by YouTube"'
        )
        download_url = ydl.extract_info(url=search_url, download=False)["entries"][0][
            "webpage_url"
        ]
        track_config["download_url"] = download_url.replace("www", "m")

    config["tracks"][track_id] = track_config

    ydl_opts = {
        "format": "mp3/bestaudio/best",
        "outtmpl": track_config["file"],
        "quiet": True,
        "no_warnings": True,
        "extractor_retries": 3,
        "postprocessors": [
            {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"},
        ],
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        error_code = ydl.download(track_config["download_url"])

    audio = MP3(track_config["file"], ID3=EasyID3)
    for attribue, value in track_config["metadata"].items():
        audio[attribue] = value
    audio.save()

    audio = MP3(track_config["file"], ID3=ID3)
    audio.tags["COMM:DLU:ENG"] = COMM(
        encoding=0,
        lang="ENG",
        desc="download_url",
        text=[track_config["download_url"]],
    )
    audio.tags["COMM:AWU:ENG"] = COMM(
        encoding=0,
        lang="ENG",
        desc="artwork_url",
        # text=[track_config["artwork"]["url"]],
        text=[track_config["artwork_url"]],
    )
    audio.tags["APIC"] = APIC(
        encoding=0,
        mime="image/jpeg",
        type=3,
        desc="Cover",
        # data=config["artwork"][track_config["artwork"]["id"]],
        data=config["artwork"][track_config["artwork_url"]],
    )
    audio.save()

    # config["tracks"][resp["id"]] = track_config


def download_album(album_id, output_dir=""):
    album = sp.album(album_id)
    tracks = sp.album_tracks(album_id, limit=50)["items"]
    for track in tracks:
        download_track(track["id"], f"{output_dir}\\{album['name']}")


def download_playlist(playlist_id, output_dir=""):
    playlist = sp.playlist(playlist_id)
    tracks = []
    while len(tracks) < playlist["tracks"]["total"]:
        tracks += [
            track["track"]["id"]
            for track in sp.playlist_items(playlist_id, limit=5, offset=len(tracks))[
                "items"
            ]
        ]
    for track in tracks:
        download_track(track, f"{output_dir}\\{playlist['name']}")


# download_album("3lS1y25WAhcqJDATJK70Mq", f"C:\\Users\\rasthmatic\\Music")

download_track("7BmpRLqZg1vLheYi1SI1Rw")
download_track("27hhIs2fp6w06N5zx4Eaa5")
# download_track("4NTUtKqXiuqTTfEBgXyVRB")
# download_playlist("1xJ5wc462pOf6BnrdAy1tl", f"C:\\Users\\rasthmatic\\Music")
# download_playlist("37i9dQZF1DZ06evO0BCJ24", f"C:\\Users\\rasthmatic\\Music")
download_album("3lS1y25WAhcqJDATJK70Mq", f"C:\\Users\\rasthmatic\\Music")

with open(f"state_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.json", "w") as cf:
    json.dump(config["tracks"], cf, indent=4)

print(config["artwork"].keys())
