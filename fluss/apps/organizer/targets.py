from pathlib import Path, PurePath
from typing import List, Union
from io import BytesIO
from parse import parse

from fluss.config import global_config
from fluss.codecs import codec_from_name, codec_from_filename

# readable suffixes supported by pillow
PILLOW_SUFFIXES = ['png', 'jpg', 'bmp', 'tiff']

class OrganizeTarget:
    description = "Target"

    def __init__(self, input_files: List[Union[str, "OrganizeTarget"]]):
        if not isinstance(input_files, list):
            self._input = [input_files]
        else:
            self._input = input_files
        self.temporary = False

    def switch_temporary(self):
        self.temporary = not self.temporary

    @classmethod
    def validate(self, input_files: List[Union[str, "OrganizeTarget"]]):
        return False

    @property
    def output_name(self):
        ''' output file name'''
        raise NotImplementedError("Abstract property!")

    def apply(self, input_root: Path = None, output_root: Path = None):
        ''' execute target
        input_root is used when input is str
        output_root is used when this target is not marked as temporary
        Should return the path to result file
        '''
        raise NotImplementedError("Abstract property!")

    def apply_stream(self, input_root: Path = None) -> BytesIO:
        ''' execute target to BytesIO
        Should return the generated binary data
        '''
        raise NotImplementedError("Abstract property!")


def _split_name(target: Union[str, OrganizeTarget]):
    if isinstance(target, str):
        name = target
    else: # OrganizeTarget
        name = target.output_name
    split = name.rsplit(".", 1)
    if len(split) == 1:
        return split[0], ""
    else:
        return split

class CopyTarget(OrganizeTarget):    
    description = "Copy"

    def __init__(self, input_files):
        super().__init__(input_files)
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        if isinstance(self._input[0], str):
            self._outname = PurePath(self._input[0]).name
        elif isinstance(self._input[0], OrganizeTarget):
            self._outname = self._input[0].output_name
        else:
            raise ValueError("Incorrect input type!")

    @classmethod
    def validate(self, input_files):
        return len(input_files) == 1 # only support one files

    @property
    def output_name(self):
        return self._outname

class TranscodeTrackTarget(OrganizeTarget):
    ''' Support recoding single audio files '''
    description = "Transcode Tracks"
    # TODO: implement track conversion (This is useful for DSD)

class ConvertTracksTarget(OrganizeTarget):
    ''' Support recoding, merging, embedding cue and embedding cover
    only allow 1 cover, 1 cue, n audio files
    '''
    description = "Convert Tracks"

    def __init__(self, input_files, codec=global_config.organizer.output_codec.audio, split_tracks=False):
        super().__init__(input_files)

        self._outstem = "" # empty means using default name
        if codec in global_config.audio_codecs:
            self._codec = codec
        else:
            self._codec = global_config.organizer.output_codec.audio

        self._tracks, self._cue, self._cover, unknown_files = ConvertTracksTarget._sort_files(input_files)
        self._tracks.sort()
        if len(unknown_files) > 0:
            raise ValueError("Not all input files are accepted.")

        self._meta = None
        self._split_tracks = split_tracks

    @staticmethod
    def _sort_files(input_files):
        cue_file = None
        cover_file = None
        audio_files = []
        unknown_files = []

        for fin in input_files:
            suffix = _split_name(fin)[1]
            if not suffix:
                unknown_files.append(fin)
            elif suffix in global_config.audio_codecs:
                audio_files.append(fin)
            elif suffix == 'cue':
                if cue_file is None:
                    cue_file = fin
                else:
                    unknown_files.append(fin)
            elif suffix in PILLOW_SUFFIXES:
                if cover_file is None:
                    cover_file = fin
                else:
                    unknown_files.append(fin)
            else:
                unknown_files.append(fin)

        return audio_files, cue_file, cover_file, unknown_files

    @classmethod
    def validate(cls, input_files):
        _, _, _, unknown_files = ConvertTracksTarget._sort_files(input_files)
        return len(unknown_files) == 0

    def _default_output_name(self):
        # TODO: use catalog if available
        if len(self._tracks) == 1:
            return "CDImage"
        else:
            return "Merged"

    @property
    def output_name(self):
        fname = self._outstem or self._default_output_name()
        codec_cls = codec_from_name[global_config.audio_codecs[self._codec].type]
        return fname + "." + codec_cls.suffix

class TranscodeTextTarget(OrganizeTarget):
    ''' Support text encoding fixing '''
    description = "Transcode Text"
    valid_encodings = ['utf-8', 'utf-8-sig', 'gb2312', 'big5', 'gbk', 'shift_jis']
    valid_file_types = ['txt', 'log', 'cue']

    def __init__(self, input_files, encoding="utf-8"):
        super().__init__(input_files)
        if encoding in self.valid_encodings:
            self._encoding = encoding
        else:
            self._encoding = "utf-8"
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        if isinstance(self._input[0], str):
            self._outname = PurePath(self._input[0]).name
        elif isinstance(self._input[0], OrganizeTarget):
            self._outname = self._input[0].output_name
        else:
            raise ValueError("Incorrect input type!")

    @classmethod
    def validate(cls, input_files):
        if len(input_files) != 1:
            return False
        suffix = _split_name(input_files[0])[1]
        if suffix not in cls.valid_file_types:
            return False
        return True

    @property
    def output_name(self):
        return self._outname

    def apply_stream(self, input_root: Path):
        content = Path(input_root, self._input[0]).read_bytes()
        return BytesIO(content.decode(encoding=self._encoding, errors="replace").encode('utf-8-sig'))

class TranscodePictureTarget(OrganizeTarget):
    ''' Support transcoding '''
    description = "Transcode Image"

    def __init__(self, input_files, codec=global_config.organizer.output_codec.image):
        super().__init__(input_files)
        if codec in global_config.image_codecs:
            self._codec = codec
        else:
            self._codec = global_config.organizer.output_codec.image
        assert len(self._input) == 1, "CopyTarget only accept one input!"

        if isinstance(self._input[0], str):
            self._outstem = PurePath(self._input[0]).stem
        elif isinstance(self._input[0], OrganizeTarget):
            self._outstem = self._input[0].output_name.rsplit('.', 1)[0]
        else:
            raise ValueError("Incorrect input type!")

    @property
    def output_name(self):
        return self._outstem + "." + global_config.image_codecs[self._codec].type

    @classmethod
    def validate(cls, input_files):
        if len(input_files) != 1:
            return False
        suffix = _split_name(input_files[0])[1]
        if suffix not in PILLOW_SUFFIXES:
            return False
        return True

class CropPictureTarget(OrganizeTarget):
    ''' Support cover cropping '''
    description = "Crop Image"

    # TODO: support this

target_types = [
    CopyTarget,
    CropPictureTarget,
    ConvertTracksTarget,
    TranscodeTrackTarget,
    TranscodeTextTarget,
    TranscodePictureTarget,
]
