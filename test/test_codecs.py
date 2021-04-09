import asyncio
from io import BytesIO
from pathlib import Path

import mutagen
from fluss import codecs, cuesheet
from fluss.cuesheet import Cuesheet
from fluss.meta import DiscMeta
from fluss.utils import merge_tracks

def test_codecs():
    wavfile = Path(r"c:/Users/cmput/Music/test.wav")
    async def test_codec(type):
        c = type()
        await c.encode_async("temp." + type.suffix, wavfile.read_bytes(), progress_callback=lambda q: print("Encoding %.3f" % q))
        w = await c.decode_async("temp." + type.suffix, progress_callback=lambda q: print("Decoding %.3f" % q))
        print(w)

    # asyncio.run(test_codec(codecs.monkeysaudio))
    # asyncio.run(test_codec(codecs.flac))
    # asyncio.run(test_codec(codecs.wavpack))
    asyncio.run(test_codec(codecs.trueaudio))

def test_combine_stream():
    from mutagen.flac import FLAC
    from mutagen.wavpack import WavPack

    cue = Cuesheet.from_file(cue_file, encoding="gbk")
    meta = asyncio.run(merge_tracks(files, "./temp.flac", cuesheet=cue, dry_run=False, progress_callback=lambda q: print(q)))
    print(meta.cuesheet)

if __name__ == "__main__":
    test_combine_stream()
