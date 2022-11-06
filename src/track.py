from utils import track_length
from yt_dlp import YoutubeDL
import json

from typing import Any
import sys


class Track:
    def __init__(self, track_id, output_dir, spotify=None, json=None) -> None:
        self.id = track_id
        self.output_dir = output_dir
        if spotify:
            self.metadata = self.get_metadata(spotify)
            self.output_file = self.get_output_file(output_dir)
            self.artwork_url = self.get_artwork_url(spotify["album"]["images"])
            self.download_url = self.get_download_url()
        elif json:
            # print(json)
            self.metadata = json["metadata"]
            self.output_file = json["output_file"]
            self.artwork_url = json["artwork_url"]
            self.download_url = json["download_url"]
        else:
            raise Exception("Either spotify or json, not both")

    def get_metadata(self, resp):
        return {
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

    def get_output_file(self, output_dir):
        file_name = "".join(e for e in self.metadata["title"] if e.isalnum())
        return f"{output_dir}\\{file_name}.mp3"

    def get_artwork_url(self, album_images):
        max_image = sorted(album_images, key=lambda i: i["height"], reverse=True)[0]
        return max_image["url"]

    def get_download_url(self):
        ydl_opts = {"noplaylist": True, "quiet": True, "no_warnings": True}
        with YoutubeDL(ydl_opts) as ydl:
            search = "".join(
                (
                    "ytsearch1:",
                    self.metadata["artist"].split(";")[0],
                    f"{self.metadata['title']} ",
                    '"Auto-generated by YouTube"',
                )
            )
            results = ydl.extract_info(url=search, download=False)
            return results["entries"][0]["webpage_url"]

    def __getitem__(self, __key):
        return vars(self)[__key]

    def __setitem__(self, __key, __value) -> None:
        vars(self)[__key] = __value

    def __repr__(self) -> str:
        return repr(vars(self))


class TrackEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if isinstance(o, Track):
            return vars(o)
        else:
            return super().default(o)


class TrackDecoder(json.JSONDecoder):
    def __init__(self):
        json.JSONDecoder.__init__(self, object_hook=self.object_hook)

    def object_hook(self, dct):
        if "id" in dct:
            print(dct)
            return Track(dct["id"], "h", json=dct)
        else:
            return dct
