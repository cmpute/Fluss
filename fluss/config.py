import addict

global_config = addict.Dict()

# path to encoders and decoders
global_config.path.wavpack = r"C:\Users\cmput\Documents\Workspace\Fluss\codecs\wavpack_x64.exe"
global_config.path.wvunpack = r"C:\Users\cmput\Documents\Workspace\Fluss\codecs\wvunpack.exe"
global_config.path.flac = r"C:\Users\cmput\Documents\Workspace\Fluss\codecs\flac_x64.exe"

# encoder preset configs
global_config.audio_codecs.wavpack.type = "wavpack"
global_config.audio_codecs.wavpack.encode = ["-m"]
global_config.audio_codecs.wavpack_hybrid.type = "wavpack"
global_config.audio_codecs.wavpack_hybrid.encode = ["-m", "-b192"]
global_config.audio_codecs.flac.type = "flac"
global_config.audio_codecs.flac.encode = []
global_config.image_codecs.png.type = "png"
global_config.image_codecs.jpg.type = "jpg"

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
