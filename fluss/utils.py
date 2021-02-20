from typing import List, Union

import mutagen
from fluss import codecs
from fluss.cuesheet import Cuesheet, _default_cuesheet_file
from fluss.meta import DiscMeta
from pathlib import Path
from io import BytesIO

def merge_tracks(files_in: List[Union[str, Path]],
                 file_out: Union[str, Path],
                 cuesheet: Union[str, Path, Cuesheet] = None,
                 dry_run: bool = False):
    '''
    Generated metadata will be returned

    :param dry_run: if true, only parse metadata
    :param cuesheet: if cuesheet is specified, meta data from cuesheet will have higher priority than from file
    '''
    if cuesheet is None:
        cuesheet = Cuesheet()
    elif isinstance(cuesheet, (str, Path)):
        cuesheet = Cuesheet.from_file(cuesheet)

    # merge audio structures
    tracks = {}
    for file_tracks in cuesheet.files.values():
        for tridx, tr in file_tracks.items():
            if tridx not in tracks:
                tracks[tridx] = tr
            else:
                tracks[tridx].update(tr)
                tracks[tridx].index00 *= -1 # mark the gap appended to previous track
    cuesheet.files.clear()
    cuesheet.files[_default_cuesheet_file] = tracks

    # load metadata from cuesheet
    meta = DiscMeta.from_cuesheet(cuesheet)

    # parse metadata and cuesheet
    offset = 0
    last_length = None
    streams = []
    for idx, file in enumerate(files_in):
        codec_t = codecs.codec_from_filename(file)
        codec = codec_t()
        mutag = codec.mutagen(file)
        track_meta = DiscMeta.from_mutagen(mutag)
        cuesheet.update(track_meta.to_cuesheet(), overwrite=False)
        meta.update(track_meta, overwrite=False)

        # process pregap
        cur_track = tracks[idx + 1]
        if cur_track.pregap is not None:
            if cur_track.index00 < 0:
                raise SyntaxError("Should not add pregap in noncompliant cuesheet")
            offset += cur_track.pregap
            streams.append(cur_track.pregap / 75.)
            cur_track.pregap = None

        # update offset
        if not dry_run:
            streams.append(codec.decode(file))
        if cur_track.index00 is not None:
            if cur_track.index00 >= 0:
                cur_track.index00 += offset
            else:
                if last_length is None:
                    raise SyntaxError("Cannot parse noncompliant pregap in the first track!")
                cur_track.index00 = (offset - last_length) + -cur_track.index00
        if cur_track.index01 is None:
            cur_track.index01 = offset
        else:
            cur_track.index01 += offset

        # process postgap
        if cur_track.postgap is not None:
            offset += cur_track.postgap
            streams.append(cur_track.postgap / 75.)
            cur_track.postgap = None

        last_length = int(mutag.info.length * 75)
        offset += last_length

    # update and assign cuesheet
    cuesheet.update(meta.to_cuesheet())
    meta.cuesheet = cuesheet

    # convert audio
    if not dry_run:
        buf = BytesIO()
        codecs.merge_streams(streams, buf)
        codec_t = codecs.codec_from_filename(file_out)
        codec = codec_t()
        codec.encode(file_out, buf.getvalue())
        mutag = codec.mutagen(file_out)
        meta.to_mutagen(mutag)
        mutag.save()

    return meta
