using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using JacobZ.Fluss.Utils;
using SharpCompress.Archives;
using ImageMagick;

namespace JacobZ.Fluss.Operation
{
    public class RecodeImage : IArchiveEntryOperation
    {
        public struct Meta
        {
            public short CompressionRate { get; set; }
            public bool Optimize { get; set; }
            public ImageCodecType Type { get; set; }
        }
        Meta _props = new Meta() { CompressionRate = 75 };
        public object Properties { get => _props; set => _props = (Meta)value; }

        public string[] Pass(params IArchiveEntry[] archiveEntries)
        {
            if (archiveEntries.Length > 1) return null;
            var fname = archiveEntries[0].Key;
            var fext = Path.GetExtension(fname).ToLower();
            var oname = Path.GetFileNameWithoutExtension(fname);

            // Check input
            var tdec = ImageCodecFactory.ParseCodec(fext);
            if (tdec == ImageCodecType.Unknown) return null;
            else if (_props.Type == ImageCodecType.Unknown)
                _props.Type = ImageCodecType.PNG; // Use png as default

            // Generate output
            switch (_props.Type)
            {
                case ImageCodecType.BMP:
                    return new string[] { oname + ".bmp" };
                case ImageCodecType.JPG:
                    return new string[] { oname + ".jpg" };
                case ImageCodecType.PNG:
                    return new string[] { oname + ".png" };
                case ImageCodecType.TIFF:
                    return new string[] { oname + ".tiff" };
                case ImageCodecType.Unknown:
                default: return null;
            }
        }

        public void Execute(IArchiveEntry[] archiveEntries, params string[] outputPath)
        {
            MagickImage img;
            using (var fin = archiveEntries[0].OpenEntryStream())
                img = new MagickImage(fin);

            img.Format = (MagickFormat)_props.Type;
            img.Quality = _props.CompressionRate;
            img.Write(outputPath[0]);

            if (_props.Optimize)
                new ImageOptimizer().LosslessCompress(outputPath[0]);
        }
    }
}
