import addict

global_config = addict.Dict()

global_config.path.wavpack = r"D:\Github\fluss\codecs\wavpack_x64.exe"
global_config.path.wvunpack = r"D:\Github\fluss\codecs\wvunpack.exe"
global_config.path.flac = r"D:\Github\fluss\codecs\flac_x64.exe"

# define possible output formats
global_config.output_format.indie = ""
global_config.output_format.commercial = ""
global_config.output_format.acg = ""
global_config.output_format.indie_collection = ""
