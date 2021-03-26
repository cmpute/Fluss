import addict

global_config = addict.Dict()

# path to encoders and decoders
global_config.path.wavpack = r"D:\Github\fluss\codecs\wavpack_x64.exe"
global_config.path.wvunpack = r"D:\Github\fluss\codecs\wvunpack.exe"
global_config.path.flac = r"D:\Github\fluss\codecs\flac_x64.exe"

# encoder configs
global_config.codecs.wavpack.type = "wavpack"
global_config.codecs.wavpack.encode = ["-m"]
global_config.codecs.wavpack.decode = [""]
global_config.codecs.wavpack_hybrid.type = "flac"
global_config.codecs.wavpack_hybrid.encode = ["-m", "-b192"]
global_config.codecs.wavpack_hybrid.decode = [""]

# define possible output formats
global_config.organizer.output_format.indie = ""
global_config.organizer.output_format.commercial = ""
global_config.organizer.output_format.acg = ""
global_config.organizer.output_format.indie_collection = ""

# define default output codec for various contents
global_config.organizer.output_codec.image = "png"
global_config.organizer.output_codec.audio = "wavpack_hybrid"
global_config.organizer.output_codec.text = "utf-8-sig"

# TODO: load config from json/yaml/toml
