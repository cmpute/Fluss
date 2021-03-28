import asyncio
import io
import subprocess
import wave
from pathlib import Path
from typing import List, Type, Union

from fluss.config import global_config as C
import mutagen
import mutagen.flac
import mutagen.wavpack
import mutagen.apev2

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
        proc = subprocess.Popen([C.path.flac, "-sV", "-", "-o", fout] + self.encode_args, stdin=subprocess.PIPE)
        proc.communicate(wavein)

    def decode(self, fin: str) -> wave.Wave_read:
        proc = subprocess.Popen([C.path.flac, "-sdc", fin], stdout=subprocess.PIPE)
        outs, _ = proc.communicate()
        return wave.open(io.BytesIO(outs), "rb")

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
        proc = subprocess.Popen([C.path.wavpack, '-yq'] + self.encode_args + ["-", fout], stdin=subprocess.PIPE)
        proc.communicate(wavein)

    def decode(self, fin: str):
        proc = subprocess.Popen([C.path.wvunpack, '-yq', fin, "-"], stdout=subprocess.PIPE)
        outs, _ = proc.communicate()
        return wave.open(io.BytesIO(outs), "rb")

    @classmethod
    def mutagen(cls, fin: str) -> mutagen.wavpack.WavPack:
        return mutagen.wavpack.WavPack(fin)

codec_from_name = {
    'wavpack': wavpack,
    'flac': flac,
}

def codec_from_filename(filename: str) -> Type[AudioCodec]:
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
        elif isinstance(wave_in, float):
            # nchannels * sampwidth * framerate * time
            wave_out.writeframes(b'\0' * int(params[0]*params[1]*params[2]*wave_in))
        else:
            raise ValueError("Unsupported stream type!")
