import asyncio
from io import BytesIO
from pathlib import Path

import mutagen
from fluss import codecs, cuesheet
from fluss.cuesheet import Cuesheet
from fluss.meta import DiscMeta
from fluss.utils import merge_tracks


def test_combine_stream():
    from mutagen.flac import FLAC
    from mutagen.wavpack import WavPack

    cue = Cuesheet.from_file(cue_file, encoding="gbk")
    meta = asyncio.run(merge_tracks(files, "./temp.flac", cuesheet=cue, dry_run=False, progress_callback=lambda q: print(q)))
    print(meta.cuesheet)

if __name__ == "__main__":
    test_combine_stream()
