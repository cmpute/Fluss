import addict

global_config = addict.Dict()

# path to encoders and decoders
global_config.path.wavpack = r"D:\Github\fluss\codecs\wavpack.exe"
global_config.path.wvunpack = r"D:\Github\fluss\codecs\wvunpack.exe"
global_config.path.flac = r"D:\Github\fluss\codecs\flac.exe"
global_config.path.mac = r"D:\Github\fluss\codecs\mac.exe"
global_config.path.tta = r"D:\Github\fluss\codecs\tta_sse4.exe"

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
global_config.organizer.output_format.indie = "[{artist}][{partnumber}][{yymmdd}({event})][{collaboration}] {title}"
global_config.organizer.output_format.commercial = "[{artist}][{yymmdd}({event})][{partnumber}] {title}"
global_config.organizer.output_format.acg = "[{yymmdd}({event})][{artist}][{partnumber}] {title}"
global_config.organizer.output_format.indie_collection = "[{partnumber}][{yymmdd}({event})] {title}"

# define default output codec for various contents
global_config.organizer.output_codec.image = "png"
global_config.organizer.output_codec.audio = "wavpack_hybrid"
global_config.organizer.output_codec.text = "utf-8-sig"

# TODO: load config from json/yaml/toml
