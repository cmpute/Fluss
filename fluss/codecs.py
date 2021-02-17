import asyncio
import io
import subprocess
import wave
from pathlib import Path
from typing import List

from fluss.config import global_config as C
import mutagen.flac
import mutagen.apev2

class Codec:
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

    def encode(self, fout: str, wavein: bytes):
        raise NotImplementedError("Abstract function!")

    def decode(self, fin: str) -> wave.Wave_read:
        raise NotImplementedError("Abstract function!")

    def __str__(self):
        if self.encode_args:
            return f"{self.__class__.__name__} ({' '.join(self.encode_args)})"
        else:
            return f"{self.__class__.__name__} (default)"

class flac(Codec):
    def __init__(self, encode_args=None):
        super().__init__(encode_args)
        assert Path(C.path.flac).exists()

    def encode(self, fout: str, wavein: bytes):
        proc = subprocess.Popen([C.path.flac, "-sV", "-", "-o", fout] + self.encode_args, stdin=subprocess.PIPE)
        proc.communicate(wavein)

    def decode(self, fin: str) -> wave.Wave_read:
        proc = subprocess.Popen([C.path.flac, "-sdc", fin], stdout=subprocess.PIPE)
        outs, _ = proc.communicate()
        return wave.open(io.BytesIO(outs), "rb")

    def parse_meta(self, fin: str):
        return mutagen.flac.FLAC(fin)

class wavpack(Codec):
    def __init__(self, encode_args=None):
        super().__init__(encode_args)
        assert Path(C.path.wavpack).exists()
        assert Path(C.path.wvunpack).exists()

    def encode(self, fout: str, wavein: bytes):
        proc = subprocess.Popen([C.path.wavpack, '-yq'] + self.encode_args + ["-", fout], stdin=subprocess.PIPE)
        proc.communicate(wavein)

    def decode(self, fin: str):
        proc = subprocess.Popen([C.path.wvunpack, '-yq', fin, "-"], stdout=subprocess.PIPE)
        outs, _ = proc.communicate()
        return wave.open(io.BytesIO(outs), "rb")

    def parse_meta(self, fin: str):
        return mutagen.apev2.APEv2File(fin)

def merge_streams(streams: List[wave.Wave_read], fout: io.RawIOBase) -> None:
    '''
    Merge audio streams and return merged streams and cuesheet
    '''
    inited = False
    wave_out = wave.open(fout, "wb")

    for wave_in in streams:
        if not inited:
            wave_out.setparams(wave_in.getparams())
            inited = True
        wave_out.writeframes(wave_in.readframes(wave_in.getnframes()))
