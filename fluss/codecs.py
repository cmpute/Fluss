'''
async decoding will use temp file to store results first due to performance issue of Python pipe and qasync (see https://github.com/CabbageDevelopment/qasync/issues/43)
'''

# TODO: check return code for all encoders

import asyncio
import io
import re
import subprocess
import wave
import tempfile
from tempfile import TemporaryDirectory, TemporaryFile
from pathlib import Path
from typing import Any, Callable, List, Type, Union, Coroutine
import logging
import random

_logger = logging.getLogger("fluss")

import mutagen
import mutagen.flac
import mutagen.wave
import mutagen.wavpack
import mutagen.monkeysaudio
import mutagen.trueaudio
import mutagen.tak
import mutagen.mp4

from mutagen import id3, apev2

from fluss.config import global_config as C

APETagFiles = (apev2.APEv2File,)
ID3TagFiles = (id3.ID3FileType, mutagen.wave.WAVE)

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

def joint_command_args(*args):
    return '"' + '" "'.join(a for a in args) + '"'

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
            convert: Union[Callable[[str], float], float],
            callback: Callable[[float], None],
            linesep: str = b'\r\b') -> None:
        '''
        Utility function for codecs to match progress string from process stream
        '''
        pattern = re.compile(pattern)
        cumulate = 0.0
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
                if isinstance(convert, float):
                    cumulate += convert
                    callback(cumulate)
                else:
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

class wav(AudioCodec):
    suffix = "wav"

    def __init__(self, encode_args=None):
        super().__init__(encode_args)

    def encode(self, fout: str, wavein: bytes) -> None:
        Path(fout).write_bytes(wavein)

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None]) -> Coroutine[Any, Any, None]:
        self.encode(fout, bytes)
        if progress_callback:
            progress_callback(1.0)

    def decode(self, fin: str) -> wave.Wave_read:
        return wave.open(Path(fin).open("rb"), "rb")

    async def decode_async(self, fin: str, progress_callback: Callable[[float], None]) -> Coroutine[Any, Any, wave.Wave_read]:
        result = self.decode(fin)
        if progress_callback:
            progress_callback(1.0)
        return result

    @classmethod
    def mutagen(cls, fin: str) -> mutagen.FileType:
        return mutagen.wave.WAVE(fin)

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

        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stdin=subprocess.PIPE, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}(?=% complete)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'ratio')

        proc.stdin.write(wavein)
        proc.stdin.close()

        if progress_callback is not None:
            _, retcode = await asyncio.gather(ptask, proc.wait())
        else:
            retcode = await proc.wait()
        if retcode != 0:
            raise RuntimeError("flac encoder returns %d" % retcode)

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

        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                pattern=rb'1?[0-9]{0,2}(?=% complete)',
                                                convert=lambda s: int(s) / 100,
                                                callback=progress_callback,
                                                linesep=b'\b')

        if progress_callback is not None:
            _, retcode = await asyncio.gather(ptask, proc.wait())
        else:
            retcode = await proc.wait()
        if retcode != 0:
            raise RuntimeError("flac decoder returns %d" % retcode)

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
        _logger.info("Encoding as wavpack to %s", fout)

        if progress_callback is None:
            args = [C.path.wavpack, '-yq'] + self.encode_args + ["-", _resolve_pathstr(fout)]
            stderr = None
        else:
            args = [C.path.wavpack, '-y'] + self.encode_args + ["-", _resolve_pathstr(fout)]
            stderr = subprocess.PIPE

        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stdin=subprocess.PIPE, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}(?=% done)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'...')

        proc.stdin.write(wavein)
        proc.stdin.close()

        if progress_callback is not None:
            _, retcode = await asyncio.gather(ptask, proc.wait())
        else:
            retcode = await proc.wait()
        if retcode != 0:
            raise RuntimeError("wavpack encoder returns %d" % retcode)

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

        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}(?=% done)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'...')

        if progress_callback is not None:
            _, retcode = await asyncio.gather(ptask, proc.wait())
        else:
            retcode = await proc.wait()
        if retcode != 0:
            raise RuntimeError("wavpack decoder returns %d" % retcode)

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
        _logger.info("Encoding as ape to %s", fout)

        with TemporaryDirectory() as tmp:
            tmp_file = Path(tmp, 'tmp.wav')
            tmp_file.write_bytes(wavein)

            args = [C.path.mac, str(tmp_file), _resolve_pathstr(fout)] + self.encode_args
            stderr = None if progress_callback is None else subprocess.PIPE
            proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stderr=stderr)

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
        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stderr=stderr)

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

# TODO: tta encoder seems to buffer stderr output
class trueaudio(AudioCodec):
    suffix = "tta"

    def __init__(self, encode_args=None):
        super().__init__(encode_args)
        assert Path(C.path.tta).exists()

    def encode(self, fout: str, wavein: bytes) -> None:
        proc = subprocess.Popen([C.path.tta, "-e"] + self.encode_args + ["-", _resolve_pathstr(fout)], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)
        proc.communicate(wavein)

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, None]:
        _logger.info("Encoding as tta to %s", fout)

        args = [C.path.tta, "-e"] + self.encode_args + ["-", _resolve_pathstr(fout)]
        stderr = subprocess.DEVNULL if progress_callback is None else subprocess.PIPE
        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stdin=subprocess.PIPE, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}(?=%)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'\r')

        proc.stdin.write(wavein)
        proc.stdin.close()

        if progress_callback is not None:
            _, retcode = await asyncio.gather(ptask, proc.wait())
        else:
            retcode = await proc.wait()
        if retcode != 0:
            raise RuntimeError("trueaudio encoder returns %d" % retcode)

    def decode(self, fin: str) -> wave.Wave_read:
        proc = subprocess.Popen([C.path.tta, "-d", _resolve_pathstr(fin), '-'], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return wave.open(proc.stdout, "rb")

    async def decode_async(self, fin: str, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, wave.Wave_read]:
        _logger.info("Decoding %s as tta", fin)
        ftmp = _get_temp_file("decode_", ".wav")

        args = [C.path.tta, "-d", _resolve_pathstr(fin), str(ftmp)]
        stderr = subprocess.DEVNULL if progress_callback is None else subprocess.PIPE
        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}(?=%)',
                                                 convert=lambda s: int(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'\r')

        if progress_callback is not None:
            _, retcode = await asyncio.gather(ptask, proc.wait())
        else:
            retcode = await proc.wait()
        if retcode != 0:
            raise RuntimeError("trueaudio decoder returns %d" % retcode)

        buf = ftmp.read_bytes()
        ftmp.unlink()
        _logger.info("Decoding %s done")
        return wave.open(io.BytesIO(buf), 'rb')

    @classmethod
    def mutagen(cls, fin: str) -> id3.ID3FileType:
        return mutagen.trueaudio.TrueAudio(fin)

class tak(AudioCodec):
    suffix = "tak"

    def __init__(self, encode_args=None):
        super().__init__(encode_args)
        assert Path(C.path.takc).exists()

    def encode(self, fout: str, wavein: bytes) -> None:
        proc = subprocess.Popen([C.path.takc, "-e", "-silent", "-overwrite"] + self.encode_args + ["-", _resolve_pathstr(fout)],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
        proc.communicate(wavein)

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, None]:
        _logger.info("Encoding as tak to %s", fout)

        args = [C.path.takc, "-e", "-overwrite"] + self.encode_args + ["-", _resolve_pathstr(fout)]
        stdout = subprocess.DEVNULL if progress_callback is None else subprocess.PIPE
        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stdin=subprocess.PIPE, stdout=stdout)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stdout,
                                                 pattern=rb'[^1-9]\.|^\.',
                                                 convert=0.1,
                                                 callback=progress_callback,
                                                 linesep=b'.')

        proc.stdin.write(wavein)
        proc.stdin.close()

        if progress_callback is not None:
            _, retcode = await asyncio.gather(ptask, proc.wait())
        else:
            retcode = await proc.wait()
        if retcode != 0:
            raise RuntimeError("tak encoder returns %d" % retcode)

    def decode(self, fin: str) -> wave.Wave_read:
        proc = subprocess.Popen([C.path.takc, "-d", "-silent", "-overwrite", _resolve_pathstr(fin), '-'],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return wave.open(proc.stdout, "rb")

    async def decode_async(self, fin: str, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, wave.Wave_read]:
        _logger.info("Decoding %s as tak", fin)
        ftmp = _get_temp_file("decode_", ".wav")

        args = [C.path.takc, "-d", "-overwrite", _resolve_pathstr(fin), str(ftmp)]
        stdout = subprocess.DEVNULL if progress_callback is None else subprocess.PIPE
        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stdout=stdout)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stdout,
                                                 pattern=rb'[^1-9]\.|^\.',
                                                 convert=0.1,
                                                 callback=progress_callback,
                                                 linesep=b'.')

        if progress_callback is not None:
            _, retcode = await asyncio.gather(ptask, proc.wait())
        else:
            retcode = await proc.wait()
        if retcode != 0:
            raise RuntimeError("tak decoder returns %d" % retcode)

        buf = ftmp.read_bytes()
        ftmp.unlink()
        _logger.info("Decoding %s done")
        return wave.open(io.BytesIO(buf), 'rb')

    @classmethod
    def mutagen(cls, fin: str) -> apev2.APEv2File:
        return mutagen.tak.TAK(fin)

class alac(AudioCodec):
    suffix = "m4a"

    def __init__(self, encode_args=None):
        super().__init__(encode_args)
        assert Path(C.path.refalac).exists()

    def encode(self, fout: str, wavein: bytes) -> None:
        proc = subprocess.Popen([C.path.refalac, "-s"] + self.encode_args + ["-", "-o", _resolve_pathstr(fout)],
            stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
        proc.communicate(wavein)
        return fout

    async def encode_async(self, fout: str, wavein: bytes, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, None]:
        _logger.info("Encoding as alac to %s", fout)

        args = [C.path.refalac] + self.encode_args + ["-", "-o", _resolve_pathstr(fout)]
        stderr = subprocess.DEVNULL if progress_callback is None else subprocess.PIPE
        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stdin=subprocess.PIPE, stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}\.[0-9](?=%])',
                                                 convert=lambda s: float(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'\r')

        proc.stdin.write(wavein)
        proc.stdin.close()

        if progress_callback is not None:
            _, retcode = await asyncio.gather(ptask, proc.wait())
        else:
            retcode = await proc.wait()
        if retcode != 0:
            raise RuntimeError("alac encoder returns %d" % retcode)

    def decode(self, fin: str) -> wave.Wave_read:
        proc = subprocess.Popen([C.path.refalac, "-s", "-D", _resolve_pathstr(fin), "-o", "-"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        return wave.open(proc.stdout, "rb")

    async def decode_async(self, fin: str, progress_callback: Callable[[float], None] = None) -> Coroutine[Any, Any, wave.Wave_read]:
        _logger.info("Decoding %s as alac", fin)
        ftmp = _get_temp_file("decode_", ".wav")

        args = [C.path.refalac, "-D", _resolve_pathstr(fin), "-o", str(ftmp)]
        stderr = subprocess.DEVNULL if progress_callback is None else subprocess.PIPE
        proc = await asyncio.create_subprocess_shell(joint_command_args(*args), stderr=stderr)

        if progress_callback is not None:
            ptask = self._report_encode_progress(proc.stderr,
                                                 pattern=rb'1?[0-9]{0,2}\.[0-9](?=%])',
                                                 convert=lambda s: float(s) / 100,
                                                 callback=progress_callback,
                                                 linesep=b'\r')

        if progress_callback is not None:
            _, retcode = await asyncio.gather(ptask, proc.wait())
        else:
            retcode = await proc.wait()
        if retcode != 0:
            raise RuntimeError("alac decoder returns %d" % retcode)

        buf = ftmp.read_bytes()
        ftmp.unlink()
        _logger.info("Decoding %s done")
        return wave.open(io.BytesIO(buf), 'rb')

    @classmethod
    def mutagen(cls, fin: str) -> mutagen.mp4.MP4:
        return mutagen.mp4.MP4(fin)

codec_from_name = {
    'wavpack': wavpack,
    'flac': flac,
    'monkeysaudio': monkeysaudio,
    'trueaudio': trueaudio,
    'wave': wav,
    'tak': tak,
    'm4a': alac
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
