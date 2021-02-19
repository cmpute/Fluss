# This module support operations on Sony DSF files. It exposes similar API to builtin wave module
# A large part of the code comes from https://github.com/lintweaker/python-dsd-tools/blob/master/dsdlib.py
# DSF file specs: https://dsd-guide.com/sites/default/files/white-papers/DSFFileFormatSpec_E.pdf

from chunk import Chunk
import struct
import builtins

dsf_data = {
    'hdr' : '<4sQQQ',
    'fmt' : '<4sQLLLLLLQLL',
    'data' : '<4sQ',
    'meta' : '<3s'
}

dsf_length = {}
dsf_unpacked = {}

for x in dsf_data:
    dsf_length[x] = struct.calcsize(dsf_data[x])
    dsf_unpacked[x] = struct.Struct(dsf_data[x]).unpack_from

def getmaxdsd() -> int:
    '''
    Returns max supported DSD rate. DSD64 = 1, DSD128 = 2, etc
    Current max is DSD1024
    '''
    return 5

def get_dsd_rates(base):
    '''
    Get all rates based on given base (44k1/48k) rate
    '''
    return [base * 2**(x+6) for x in range(0, getmaxdsd())]

def dsd_valid_rate(rate) -> bool:
    '''
    Check if given rate is a valid DSD rate
    '''
    if rate % 44100 == 0:
        return rate in get_dsd_rates(44100)
    if rate % 48000 == 0:
        return rate in get_dsd_rates(48000)
    return False

class Dsf_read:
    def initfp(self, f):
        self._file = f

        # Read header of the file and check for the needed DSF ID
        data = f.read(dsf_length['hdr'])
        hdr = dsf_unpacked['hdr'](data)
        if hdr[0] != b'DSD ':
            raise RuntimeError("not a DSF file!")
        if hdr[1] != 28: # chunk size
            raise RuntimeError("Wrong header chunk size: %d" % hdr[1])

        file_size = hdr[2] # not used
        self._id3_pos = hdr[3]

        # Read the fmt chunk
        data = f.read(dsf_length['fmt'])
        fmt = dsf_unpacked['fmt'](data)

        if fmt[0] != b'fmt ':
            print(fmt[0])
            raise RuntimeError("Expect fmt chunk after head")
        if fmt[1] != 52: # chunk size
            raise RuntimeError("Wrong fmt chunk size: %d" % hdr[1])
        if fmt[2] != 1: # DSF version
            raise RuntimeError("Only support DSF version 1")
        if fmt[3] != 0: # DSF format id
            raise RuntimeError("Only support DSF format 0")

        self._channel_type = fmt[4]
        if fmt[4] == 0 or fmt[4] > 7:
            raise RuntimeError("Unrecognized channel type.")

        self._nchannels = fmt[5]
        if fmt[5] == 0 or fmt[5] > 7:
            raise RuntimeError("Unrecognized channel num.")

        self._dsf_rate = fmt[6]
        if not dsd_valid_rate(fmt[6]):
            raise RuntimeError("Incorrent DSF sampling frequency!")

        self._samplewidth = 1
        if fmt[7] not in [1, 8]:
            raise RuntimeError("Incorrect bit depth")
        self._lsbfirst = fmt[7] == 1

        self._nframes = fmt[8]
        self._block_size = fmt[9]
        if fmt[9] != 4096:
            raise RuntimeError("Block size should be 4096!")

        # Read chunk header of 'data' chunk
        data = f.read(dsf_length['data'])
        db = dsf_unpacked['data'](data)

        if db[0] != b'data':
            raise RuntimeError("Expect data chunk after fmt")

        self._data_pos = f.tell()

    def __init__(self, f):
        self._i_opened_the_file = None
        if isinstance(f, str):
            f = builtins.open(f, 'rb')
            self._i_opened_the_file = f

        try:
            self.initfp(f)
        except:
            if self._i_opened_the_file:
                f.close()
            raise
