import addict

global_config = addict.Dict()

# path to encoders and decoders
global_config.path.wavpack = r"D:\Github\fluss\codecs\wavpack.exe"
global_config.path.wvunpack = r"D:\Github\fluss\codecs\wvunpack.exe"
global_config.path.flac = r"D:\Github\fluss\codecs\flac.exe"
global_config.path.mac = r"D:\Github\fluss\codecs\mac.exe"
global_config.path.tta = r"D:\Github\fluss\codecs\tta_sse4.exe"
global_config.path.arcue = r"C:\Program Files (x86)\CUETools\CUETools_2.1.6\ArCueDotNet.exe"

# encoder preset configs
global_config.audio_codecs.wavpack.type = "wavpack"
global_config.audio_codecs.wavpack.encode = ["-m"]
global_config.audio_codecs.wavpack_hybrid.type = "wavpack"
global_config.audio_codecs.wavpack_hybrid.encode = ["-m", "-b192", "-c"]
global_config.audio_codecs.wavpack_hybrid_high.type = "wavpack"
global_config.audio_codecs.wavpack_hybrid_high.encode = ["-m", "-h", "-b192", "-c", "-x"]
global_config.audio_codecs.flac.type = "flac"
global_config.audio_codecs.flac.encode = []
global_config.image_codecs.png.type = "png"
global_config.image_codecs.jpg.type = "jpeg"
global_config.image_codecs.jpg.quality = 80

# define possible output formats
global_config.organizer.output_format.indie = "[{artist}][{partnumber}][{yymmdd}({event})][{collaboration}] {title}"
global_config.organizer.output_format.commercial = "[{artist}][{yymmdd}({event})][{partnumber}] {title}"
global_config.organizer.output_format.acg = "[{yymmdd}({event})][{artist}][{partnumber}] {title}"
global_config.organizer.output_format.indie_collection = "[{partnumber}][{yymmdd}({event})] {title}"

# define default output codec for various contents
global_config.organizer.output_codec.image = "png"
global_config.organizer.output_codec.audio = "wavpack_hybrid_high"
global_config.organizer.output_codec.text = "utf-8-sig"

# some other options
global_config.organizer.artist_splitter = r",\s+|;\s+"  # regex expression for splitting artist
global_config.organizer.keyword_splitter = r';| - |\[|\]|\(|\)'  # regex expression for splitting keyword

# TODO: load config from json/yaml/toml

# setting up logging
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S',
                    filename='fluss.log',
                    filemode='w')
