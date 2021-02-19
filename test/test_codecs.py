import mutagen
from fluss.cuesheet import Cuesheet
from fluss import codecs, cuesheet
from io import BytesIO
from pathlib import Path

def test_combine_stream():
    from mutagen.flac import FLAC
    from mutagen.wavpack import WavPack

    files = [
    ]

    buf = BytesIO()
    codecs.merge_streams([codecs.flac().decode(f) for f in files], buf)
    codecs.wavpack(['-m']).encode(r'D:\Github\fluss\temp.wv', buf.getvalue())

    cue = cuesheet.Cuesheet()
    offset = 0
    for idx, file in enumerate(files):
        f = FLAC(file)

        cue.title = f.tags['ALBUM'][0]
        cue.performer = f.tags['ALBUMARTIST'][0]
        track = cuesheet.CuesheetTrack()
        track.title = f.tags['TITLE'][0]
        track.performer = f.tags['ARTIST'][0]
        track.index01 = offset
        offset += int(f.info.length * 75)
        cue.files[r'temp.wv'][idx+1] = track
    Path("./temp.cue").write_text(str(cue), encoding="utf-8-sig")

    wvtag = WavPack("./temp.wv")
    wvtag.add_tags()
    wvtag.tags['ALBUM'] = f.tags['ALBUM'][0]
    wvtag.tags['ALBUMARTIST'] = f.tags['ALBUMARTIST'][0]
    wvtag.tags['CUESHEET'] = str(cue)
    wvtag.save()

if __name__ == "__main__":
    test_combine_stream()
