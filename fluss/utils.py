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

    :param dry_run: If true, only parse metadata
    '''
    meta = DiscMeta()
    if cuesheet is None:
        cuesheet = Cuesheet()
    elif isinstance(cuesheet, (str, Path)):
        cuesheet = Cuesheet.from_file(cuesheet)

    # load cuesheet from metadata and discard multi-file cuesheet
    meta.from_cuesheet(cuesheet)
    if len(cuesheet.files) > 0:
        cuesheet = Cuesheet()

    # parse metadata and cuesheet
    offset = 0
    streams = []
    for idx, file in enumerate(files_in):
        codec_t = codecs.codec_from_filename(file)
        codec = codec_t()
        mutag = codec.mutagen(file)
        track_meta = DiscMeta.from_mutagen(mutag)
        track_meta.to_cuesheet(cuesheet) # TODO: which is higher priority
        meta.update(track_meta) # TODO: which is higher priority

        cuesheet.files[_default_cuesheet_file][idx + 1].index01 = offset
        offset += int(mutag.info.length * 75)
        
        if not dry_run:
            streams.append(codec.decode(file))

    # assign cuesheet
    meta.to_cuesheet(cuesheet)
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
