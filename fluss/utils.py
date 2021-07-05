from collections import defaultdict
from ntpath import join
from typing import Callable, List, Tuple, Union, Any
import asyncio
from PIL.Image import new

from fluss import codecs
from fluss.cuesheet import Cuesheet, _default_cuesheet_file
from fluss.meta import DiscMeta
from fluss.config import global_config
from pathlib import Path
from io import BytesIO

def _get_codec(filename: Union[str, Path], codec: str = None) -> codecs.AudioCodec:
    if codec:
        codec_conf = global_config.audio_codecs[codec]
        codec_t = codecs.codec_from_name[codec_conf.type.lower()]
        if codec_t != codecs.codec_from_filename(filename):
            raise ValueError("Inconsistent codec type with file suffix!")
        return codec_t(codec_conf.encode)
    else:
        codec_t = codecs.codec_from_filename(filename)
        return codec_t()

class _ProgressCombiner:
    '''
    Combine progress for multiple parallel tasks
    '''
    def __init__(self, identifiers: list, progress_callback: Callable[[float], None] = None, range: Tuple[float, float] = [0,1]) -> None:
        self._callback = progress_callback
        self._range = range
        self._min_progress = 0
        self._progress = {i: 0 for i in identifiers}

        if progress_callback is not None:
            progress_callback(float(range[0]))

    def call(self): 
        min_progress = min(self._progress.values())
        if self._min_progress != min_progress and self._callback is not None:
            self._callback(min_progress * (self._range[1] - self._range[0]) + self._range[0])
            self._min_progress = min_progress

    def get_updater(self, identifier: Any):
        def update(progress: float):
            self._progress[identifier] = progress
            self.call()
        return update

async def merge_tracks(files_in: List[Union[str, Path]],
                       file_out: Union[str, Path],
                       cuesheet: Union[str, Path, Cuesheet] = None,
                       meta: DiscMeta = None,
                       codec_out: str = None,
                       progress_callback: Callable[[float], None] = None,
                       dry_run: bool = False):
    '''
    Generated metadata will be returned

    :param dry_run: if true, only parse metadata
    :param cuesheet: if cuesheet is specified, meta data from cuesheet will have higher priority than from file
    :param codec_out: if not given, output codec will be infered from file name and have default parameters
    '''
    if cuesheet is None:
        if meta and meta.cuesheet:
            cuesheet = meta.cuesheet
        else:
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
    if meta is None:
        meta = DiscMeta.from_cuesheet(cuesheet)

    # parse metadata and cuesheet
    offset = 0
    last_length = None
    streams = []
    progress_updater = _ProgressCombiner(range(len(files_in)), progress_callback=progress_callback, range=[0, 0.5])
    for idx, file in enumerate(files_in):
        codec_t = codecs.codec_from_filename(file)
        icodec = codec_t()
        mutag = icodec.mutagen(file)
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
            wave_in = asyncio.ensure_future(icodec.decode_async(file,
                progress_callback=progress_updater.get_updater(idx)))
            streams.append(wave_in)
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

    # wait for completion
    tasks = [(i, s) for i, s in enumerate(streams) if isinstance(s, asyncio.Task)]
    results = await asyncio.gather(*[s for _, s in tasks])
    for (i, _), r in zip(tasks, results):
        streams[i] = r

    # update and assign cuesheet
    cuesheet.update(meta.to_cuesheet())
    meta.cuesheet = cuesheet

    # convert audio
    ocodec = _get_codec(file_out, codec_out)
    if not dry_run:
        buf = BytesIO()
        codecs.merge_streams(streams, buf)

        await ocodec.encode_async(file_out, buf.getvalue(),
            progress_callback=lambda p: progress_callback(p / 2 + 0.5))

        mutag = ocodec.mutagen(file_out)
        meta.to_mutagen(mutag)
        mutag.save()

    return meta

async def convert_track(file_in: Union[str, Path],
                        file_out: Union[str, Path],
                        meta: DiscMeta = None,
                        codec_out: str = None,
                        progress_callback: Callable[[float], None] = None,
                        dry_run: bool = False):
    '''
    Convert audio file and preserve meta data
    '''

    icodec = _get_codec(file_in)
    ocodec = _get_codec(file_out, codec_out)

    if meta is None:
        meta = DiscMeta.from_mutagen(icodec.mutagen(file_in))

    if not dry_run:
        wave_in = await icodec.decode_async(file_in,
            progress_callback=lambda p: progress_callback(p / 2))

        # get absolute data
        buf = wave_in.getfp().file
        if isinstance(buf, BytesIO):
            data = buf.getvalue()
        else:
            buf.seek(0)
            data = buf.read()
            buf.close()

        await ocodec.encode_async(file_out, data,
            progress_callback=lambda p: progress_callback(p / 2 + 0.5))
        meta.to_mutagen(ocodec.mutagen(file_out))
