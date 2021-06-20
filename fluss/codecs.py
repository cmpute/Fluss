'''
async decoding will use temp file to store results first due to performance issue of Python pipe and qasync (see https://github.com/CabbageDevelopment/qasync/issues/43)
'''

import asyncio
import io
import re
import subprocess
import wave
import tempfile
from tempfile import mkstemp, TemporaryDirectory, TemporaryFile
from pathlib import Path
from typing import Any, Callable, List, Type, Union, Coroutine
import logging
import random

_logger = logging.getLogger("fluss")

import mutagen
import mutagen.apev2
import mutagen.flac
import mutagen.wavpack
import mutagen.monkeysaudio
import mutagen.trueaudio
from mutagen import id3

from fluss.config import global_config as C

def _resolve_pathstr(file: Union[str, Path]):
    if isinstance(file, str):
        return str(Path(file).resolve())
    elif isinstance(file, Path):
        return str(file.resolve())
    else:
        raise ValueError("Incorrect path type")

def _get_temp_file(prefix='', ext=None):
    tmpfolder = Path(tempfile.gettempdir(), "fluss")
    tmpfolder.mkdir(exist_ok=True)
    fname = prefix + hex(random.getrandbits(48))[2:]
    if ext:
        fname += ext
    return tmpfolder / fname

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
            if not line:
                continue

            match = pattern.search(line)
            if match:
                callback(convert(match[0]))

    def encode(self, fout: str, wavein: bytes) -> None:
        raise NotImplementedError("Abstract function!")

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, None]:
        raise NotImplementedError("Abstract function!")

    def decode(self, fin: str) -> wave.Wave_read:
        raise NotImplementedError("Abstract function!")

    async def decode_async(self, fin: str, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, wave.Wave_read]:
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
        proc = subprocess.Popen([C.path.flac, "-sfV", "-", "-o", _resolve_pathstr(fout)] + self.encode_args, stdin=subprocess.PIPE)
        proc.communicate(wavein)

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, None]:
        _logger.info("Encoding as flac to %s", fout)

        if progress_callback is None:
            args = [C.path.flac, "-sfV", "-", "-o", _resolve_pathstr(fout)] + self.encode_args
            stderr = None
        else:
            args = [C.path.flac, "-fV", "-", "-o", _resolve_pathstr(fout)] + self.encode_args
            stderr = subprocess.PIPE

        proc = await asyncio.create_subprocess_exec(*args, stdin=subprocess.PIPE, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}(?=% complete)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'ratio')

        proc.stdin.write(wavein)
        proc.stdin.close()

        if progress_callback is not None:
            await asyncio.gather(ptask, proc.wait())
        else:
            await proc.wait()

        _logger.info("Encoding %s done")

    def decode(self, fin: str) -> wave.Wave_read:
        proc = subprocess.Popen([C.path.flac, "-sdc", _resolve_pathstr(fin)], stdout=subprocess.PIPE)
        return wave.open(proc.stdout, "rb")

    async def decode_async(self, fin: str, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, wave.Wave_read]:
        ftmp = _get_temp_file(prefix='decode_', ext='.wav')
        _logger.info("Decoding %s as flac to %s", fin, str(ftmp))

        if progress_callback is None:
            args = [C.path.flac, "-sdc", _resolve_pathstr(fin), "-o", str(ftmp)]
            stderr = None
        else:
            args = [C.path.flac, "-dc", _resolve_pathstr(fin), "-o", str(ftmp)]
            stderr = subprocess.PIPE

        proc = await asyncio.create_subprocess_exec(*args, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                pattern=rb'1?[0-9]{0,2}(?=% complete)',
                                                convert=lambda s: int(s) / 100,
                                                callback=progress_callback,
                                                linesep=b'\b')

        if progress_callback is not None:
            await asyncio.gather(ptask, proc.wait())
        else:
            await proc.wait()

        buf = ftmp.read_bytes()
        ftmp.unlink()

        _logger.info("Decoding %s done")
        return wave.open(io.BytesIO(buf), 'rb')

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

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, None]:
        if progress_callback is None:
            args = [C.path.wavpack, '-yq'] + self.encode_args + ["-", _resolve_pathstr(fout)]
            stderr = None
        else:
            args = [C.path.wavpack, '-y'] + self.encode_args + ["-", _resolve_pathstr(fout)]
            stderr = subprocess.PIPE

        proc = await asyncio.create_subprocess_exec(*args, stdin=subprocess.PIPE, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}(?=% done)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'...')

        proc.stdin.write(wavein)
        proc.stdin.close()

        if progress_callback is not None:
            await asyncio.gather(ptask, proc.wait())
        else:
            await proc.wait()

    def decode(self, fin: str) -> wave.Wave_read:
        proc = subprocess.Popen([C.path.wvunpack, '-yq', _resolve_pathstr(fin), "-"], stdout=subprocess.PIPE)
        return wave.open(proc.stdout, "rb")

    async def decode_async(self, fin: str, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, wave.Wave_read]:
        _logger.info("Decoding %s as wavpack", fin)
        ftmp = _get_temp_file("decode_", ".wav")

        if progress_callback is None:
            args = [C.path.wvunpack, '-yq', _resolve_pathstr(fin), str(ftmp)]
            stderr = None
        else:
            args = [C.path.wvunpack, '-y', _resolve_pathstr(fin), str(ftmp)]
            stderr = subprocess.PIPE

        proc = await asyncio.create_subprocess_exec(*args, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}(?=% done)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'...')

        if progress_callback is not None:
            await asyncio.gather(ptask, proc.wait())
        else:
            await proc.wait()

        buf = ftmp.read_bytes()
        _logger.info("Decoding %s done", fin)
        return wave.open(io.BytesIO(buf), 'rb')

    @classmethod
    def mutagen(cls, fin: str) -> mutagen.wavpack.WavPack:
        return mutagen.wavpack.WavPack(fin)

class monkeysaudio(AudioCodec):
    suffix = 'ape'

    def __init__(self, encode_args=None):
        if not encode_args:
            encode_args = ['-c2000'] # normal compression
        if '-c' not in ''.join(encode_args):
            encode_args.append('-c2000')
        super().__init__(encode_args=encode_args)
        assert Path(C.path.mac).exists()

    def encode(self, fout: str, wavein: bytes) -> None:
        with TemporaryDirectory() as tmp:
            tmp_file = Path(tmp, 'tmp.wav')
            tmp_file.write_bytes(wavein)
            proc = subprocess.Popen([C.path.mac, str(tmp_file), _resolve_pathstr(fout)] + self.encode_args, stderr=subprocess.DEVNULL)
            proc.wait()

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, None]:
        with TemporaryDirectory() as tmp:
            tmp_file = Path(tmp, 'tmp.wav')
            tmp_file.write_bytes(wavein)

            args = [C.path.mac, str(tmp_file), _resolve_pathstr(fout)] + self.encode_args
            stderr = None if progress_callback is None else subprocess.PIPE
            proc = await asyncio.create_subprocess_exec(*args, stderr=stderr)

            if progress_callback is not None:
                ptask = self._report_encode_progress(proc.stderr,
                                                     pattern=rb'1?[0-9]{0,2}\.[0-9](?=% \()',
                                                     convert=lambda s: float(s) / 100,
                                                     callback=progress_callback,
                                                     linesep=b')')

            if progress_callback is not None:
                await asyncio.gather(ptask, proc.wait())
            else:
                await proc.wait()

    def decode(self, fin: str) -> wave.Wave_read:
        ftmp = _get_temp_file("decode_", ".wav")
        proc = subprocess.Popen([C.path.mac, _resolve_pathstr(fin), str(ftmp), '-d'], stderr=subprocess.DEVNULL)
        proc.wait()
        buf = io.BytesIO(ftmp.read_bytes())
        ftmp.unlink()
        return wave.open(buf, "rb")

    async def decode_async(self, fin: str, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, wave.Wave_read]:
        _logger.info("Decoding %s as ape", fin)
        ftmp = _get_temp_file("decode_", ".wav")

        args = [C.path.mac, _resolve_pathstr(fin), str(ftmp), '-d']
        stderr = None if progress_callback is None else subprocess.PIPE
        proc = await asyncio.create_subprocess_exec(*args, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                    pattern=rb'1?[0-9]{0,2}\.[0-9](?=% \()',
                                                    convert=lambda s: float(s) / 100,
                                                    callback=progress_callback,
                                                    linesep=b')')

        if progress_callback is not None:
            await asyncio.gather(ptask, proc.wait())
        else:
            await proc.wait()

        buf = ftmp.read_bytes()
        ftmp.unlink()
        _logger.info("Decoding %s done")
        return wave.open(io.BytesIO(buf), 'rb')

    @classmethod
    def mutagen(cls, fin: str) -> mutagen.wavpack.WavPack:
        return mutagen.monkeysaudio.MonkeysAudio(fin)


class trueaudio(AudioCodec):
    suffix = "tta"

    def __init__(self, encode_args=None):
        super().__init__(encode_args)
        assert Path(C.path.tta).exists()

    def encode(self, fout: str, wavein: bytes) -> None:
        proc = subprocess.Popen([C.path.tta, "-e"] + self.encode_args + ["-", _resolve_pathstr(fout)], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        proc.communicate(wavein)

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, None]:
        args = [C.path.tta, "-e"] + self.encode_args + ["-", _resolve_pathstr(fout)]
        stderr = subprocess.DEVNULL if progress_callback is None else subprocess.PIPE
        proc = await asyncio.create_subprocess_exec(*args, stdin=subprocess.PIPE, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}(?=%)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'\r')

        proc.stdin.write(wavein)
        proc.stdin.close()

        if progress_callback is not None:
            await asyncio.gather(ptask, proc.wait())
        else:
            await proc.wait()

    def decode(self, fin: str) -> wave.Wave_read:
        proc = subprocess.Popen([C.path.tta, "-d", _resolve_pathstr(fin), '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return wave.open(proc.stdout, "rb")

    async def decode_async(self, fin: str, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, wave.Wave_read]:
        _logger.info("Decoding %s as tta", fin)
        ftmp = _get_temp_file("decode_", ".wav")

        args = [C.path.tta, "-d", _resolve_pathstr(fin), str(ftmp)]
        stderr = subprocess.DEVNULL if progress_callback is None else subprocess.PIPE
        proc = await asyncio.create_subprocess_exec(*args, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}(?=%)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'\r')

        if progress_callback is not None:
            await asyncio.gather(ptask, proc.wait())
        else:
            await proc.wait()

        buf = ftmp.read_bytes()
        ftmp.unlink()
        _logger.info("Decoding %s done")
        return wave.open(io.BytesIO(buf), 'rb')

    @classmethod
    def mutagen(cls, fin: str) -> id3.ID3FileType:
        return mutagen.trueaudio.TrueAudio(fin)


codec_from_name = {
    'wavpack': wavpack,
    'flac': flac,
    'monkeysaudio': monkeysaudio,
    'trueaudio': trueaudio
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
