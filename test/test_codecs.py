import mutagen
from fluss.cuesheet import Cuesheet
from fluss import codecs, cuesheet
from fluss.meta import DiscMeta
from fluss.utils import merge_tracks
from io import BytesIO
from pathlib import Path

def test_combine_stream():
    from mutagen.flac import FLAC
    from mutagen.wavpack import WavPack

    cue = Cuesheet.from_file(cue_file, encoding="gbk")
    meta = merge_tracks(files, "./temp.wv", cuesheet=cue, dry_run=False)
    print(meta.cuesheet)

if __name__ == "__main__":
    test_combine_stream()
