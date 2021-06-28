from pathlib import Path
import addict
import yaml

global_config = addict.Dict()

# path to encoders and decoders
global_config.path.wavpack = ""
global_config.path.wvunpack = ""
global_config.path.flac = ""
global_config.path.mac = ""
global_config.path.takc = ""
global_config.path.tta = ""
global_config.path.arcue = ""

# encoder preset configs
global_config.audio_codecs.wavpack.type = "wavpack"
global_config.audio_codecs.wavpack.encode = ["-m"]
global_config.audio_codecs.wavpack_hybrid.type = "wavpack"
global_config.audio_codecs.wavpack_hybrid.encode = ["-m", "-b192", "-c"]
global_config.audio_codecs.wavpack_hybrid_high.type = "wavpack"
global_config.audio_codecs.wavpack_hybrid_high.encode = ["-m", "-hx", "-b192", "-c"]
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
global_config.organizer.default_output_dir = r""
global_config.organizer.artist_splitter = r",\s+|;\s+"  # regex expression for splitting artist
global_config.organizer.keyword_splitter = r';| - |\[|\]|\(|\)'  # regex expression for splitting keyword

# load config from file
config_path = Path("~/.fluss.yaml").expanduser()
if config_path.exists():
    with config_path.open("r", encoding="utf-8-sig") as fin:
        saved_config = yaml.safe_load(fin)
        global_config.update(addict.Dict(saved_config))
else:
    with config_path.open("w", encoding="utf-8-sig") as fout:
        fout.write("# This file contains the configs for Fluss organizer.\n")
        yaml.dump(global_config.to_dict(), fout, encoding="utf-8", allow_unicode=True)

# setting up logging
import logging
logging.basicConfig(level=logging.DEBUG,
                    handlers=[logging.FileHandler(filename=Path("~/.fluss.log").expanduser(), 
                                                  encoding='utf-8', mode='a+')],
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M:%S')
