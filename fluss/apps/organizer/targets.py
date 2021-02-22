from typing import List, Union

class OrganizeTarget:
    def __init__(self, input_files: List[Union[str, "OrganizeTarget"]]):
        self._input = input_files

    @classmethod
    def validate(self, input_files: List[Union[str, "OrganizeTarget"]]):
        raise NotImplementedError("Abstract function!")

    @property
    def output_name(self):
        raise NotImplementedError("Abstract property!")

class CopyTarget(OrganizeTarget):
    def __init__(self, input_files):
        super().__init__(input_files)

        assert len(self._input) == 1, "CopyTarget only accept one input!"
        assert isinstance(self._input[0], (str, OrganizeTarget)), "Incorrect input type!"

    @classmethod
    def validate(self, input_files):
        return len(input_files) == 1 # only support one files

    @property
    def output_name(self):
        if isinstance(self._input[0], str):
            _outname = self._input[0]
        elif isinstance(self._input[0], OrganizeTarget):
            _outname = self._input[0].output_name
        return _outname

class TranscodeTracksTarget(OrganizeTarget):
    # Support recoding, merging, embedding cue and embedding cover
    pass

class TranscodeTextTarget(OrganizeTarget):
    # Support text encoding fixing
    pass

class TranscodePictureTarget(OrganizeTarget):
    # Support transcoding
    pass

class CropPictureTarget:
    # Support cover cropping
    pass
