import asyncio
import io
import re
import subprocess
import wave
from pathlib import Path
from typing import Any, Callable, List, Type, Union

import mutagen
import mutagen.apev2
import mutagen.flac
import mutagen.wavpack

from fluss.config import global_config as C

def _resolve_pathstr(file: Union[str, Path]):
    if isinstance(file, str):
        return str(Path(file).resolve())
    elif isinstance(file, Path):
        return str(file.resolve())
    else:
        raise ValueError("Incorrect path type")

class AudioCodec:
    suffix: str
    ''' output suffix of files with this codec
    '''

    def __init__(self, encode_args=None):
        '''
        encode_args: (extra) command line args for encoding, usually for adjusting compression level
        '''
        if encode_args is None:
            self.encode_args = []
        elif isinstance(encode_args, (list, tuple)):
            self.encode_args = list(encode_args)
        else:
            self.encode_args = [encode_args]

    def encode(self, fout: str, wavein: bytes) -> None:
        raise NotImplementedError("Abstract function!")

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None] = None) -> None:
        raise NotImplementedError("Abstract function!")

    async def _report_encode_progress(self,
            stream: asyncio.StreamReader,
            pattern: str,
            convert: Callable[[str], float],
            callback: Callable[[float], None],
            linesep: str = b'\r\b') -> None:
        '''
        Utility function for codecs to match progress string from process stream
        '''
        pattern = re.compile(pattern)
        finished = False
        while not finished:
            try:
                line = await stream.readuntil(linesep)
            except asyncio.exceptions.IncompleteReadError as e:
                line = e.partial
                finished = True

            match = pattern.search(line)
            if match:
                callback(convert(match[0]))

    def decode(self, fin: str) -> wave.Wave_read:
        raise NotImplementedError("Abstract function!")

    @classmethod
    def mutagen(cls, fin: str) -> mutagen.FileType:
        raise NotImplementedError("Abstract function!")

    def __str__(self):
        if self.encode_args:
            return f"{self.__class__.__name__} ({' '.join(self.encode_args)})"
        else:
            return f"{self.__class__.__name__} (default)"

class flac(AudioCodec):
    suffix = "flac"

    def __init__(self, encode_args=None):
        super().__init__(encode_args)
        assert Path(C.path.flac).exists()

    def encode(self, fout: str, wavein: bytes) -> None:
        proc = subprocess.Popen([C.path.flac, "-sV", "-", "-o", _resolve_pathstr(fout)] + self.encode_args, stdin=subprocess.PIPE)
        proc.communicate(wavein)

    def decode(self, fin: str) -> wave.Wave_read:
        proc = subprocess.Popen([C.path.flac, "-sdc", _resolve_pathstr(fin)], stdout=subprocess.PIPE)
        return wave.open(proc.stdout, "rb")

    @classmethod
    def mutagen(cls, fin: str) -> mutagen.flac.FLAC:
        return mutagen.flac.FLAC(fin)

class wavpack(AudioCodec):
    suffix = "wv"

    def __init__(self, encode_args=None):
        super().__init__(encode_args)
        assert Path(C.path.wavpack).exists()
        assert Path(C.path.wvunpack).exists()

    def encode(self, fout: str, wavein: bytes) -> None:
        proc = subprocess.Popen([C.path.wavpack, '-yq'] + self.encode_args + ["-", _resolve_pathstr(fout)], stdin=subprocess.PIPE)
        proc.communicate(wavein)

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None] = None) -> None:
        if progress_callback is None:
            args = [C.path.wavpack, '-yq'] + self.encode_args + ["-", _resolve_pathstr(fout)]
            stderr = None
        else:
            args = [C.path.wavpack, '-y'] + self.encode_args + ["-", _resolve_pathstr(fout)]
            stderr = subprocess.PIPE

        proc = await asyncio.create_subprocess_exec(*args, stdin=subprocess.PIPE, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=b'1?[0-9]{0,2}(?=% done)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'...')

        proc.stdin.write(wavein)
        proc.stdin.close()

        if progress_callback is not None:
            await asyncio.gather(ptask, proc.wait())
        else:
            await proc.wait()

    def decode(self, fin: str):
        proc = subprocess.Popen([C.path.wvunpack, '-yq', _resolve_pathstr(fin), "-"], stdout=subprocess.PIPE)
        return wave.open(proc.stdout, "rb")

    @classmethod
    def mutagen(cls, fin: str) -> mutagen.wavpack.WavPack:
        return mutagen.wavpack.WavPack(fin)

codec_from_name = {
    'wavpack': wavpack,
    'flac': flac,
}

def codec_from_filename(filename: Union[Path, str]) -> Type[AudioCodec]:
    codec_map = {('.' + c.suffix): c for c in codec_from_name.values()}
    return codec_map[Path(filename).suffix]

def merge_streams(streams: List[Union[wave.Wave_read, float]], fout: io.RawIOBase) -> None:
    '''
    Merge audio streams and return merged streams and cuesheet

    :param streams: if given float, it specifies a period of silence with given length
    '''
    params = None
    wave_out = wave.open(fout, "wb")

    for wave_in in streams:
        if params is None:
            if not isinstance(wave_in, wave.Wave_read):
                raise ValueError("Unable to insert silence at the beginning!")
            params = wave_in.getparams()
            wave_out.setparams(params)
        if isinstance(wave_in, wave.Wave_read):
            wave_out.writeframes(wave_in.readframes(wave_in.getnframes()))
            wave_in.close()
        elif isinstance(wave_in, float):
            # add silence of nchannels * sampwidth * framerate * time frames
            wave_out.writeframes(b'\0' * int(params[0]*params[1]*params[2]*wave_in))
        else:
            raise ValueError("Unsupported stream type!")
