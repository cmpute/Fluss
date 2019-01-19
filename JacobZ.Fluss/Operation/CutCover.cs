using System;
using System.Collections.Generic;
using System.IO;
using System.Text;
using ImageMagick;
using JacobZ.Fluss.Utils;
using SharpCompress.Archives;

namespace JacobZ.Fluss.Operation
{
    public class CutCover : IArchiveEntryOperation
    {
        const double DefaultShrinkRatio = 0.01;

        public struct Meta
        {
            public int CropX { get; set; }
            public int CropY { get; set; }
            public int CropSize { get; set; }
            public int OutputSize { get; set; }
        }
        Meta _props = new Meta() { OutputSize = 600 };
        public object Properties { get => _props; set => _props = (Meta)value; }

        public string[] Pass(params IArchiveEntry[] archiveEntries)
        {
            if (archiveEntries.Length > 1) return null;
            var fname = archiveEntries[0].Key;
            var fext = Path.GetExtension(fname).ToLower();

            // Check input
            var tdec = ImageCodecFactory.ParseCodec(fext);
            if (tdec == ImageCodecType.Unknown) return null;

            // Generate default crop position
            if (_props.CropX == 0)
            {
                MagickImage img;
                using (var fin = archiveEntries[0].OpenEntryStream())
                    img = new MagickImage(fin);
                _props.CropSize = img.Width > img.Height ? img.Height : img.Width;
                _props.CropX = _props.CropY = (int)(_props.CropSize * DefaultShrinkRatio);
                _props.CropSize = (int)(_props.CropSize * (1 - 2 * DefaultShrinkRatio));
            }

            // Generate output
            return new string[] { "cover.jpg" };
        }

        public void Execute(IArchiveEntry[] archiveEntries, params string[] outputPath)
        {
            MagickImage img;
            using (var fin = archiveEntries[0].OpenEntryStream())
                img = new MagickImage(fin);

            MagickGeometry size = new MagickGeometry(_props.CropX, _props.CropY, _props.CropSize, _props.CropSize);
            img.Crop(size); img.RePage();
            img.Resize(_props.OutputSize, _props.OutputSize);

            img.Format = MagickFormat.Jpeg;
            img.Write(outputPath[0]);
            new ImageOptimizer().Compress(outputPath[0]);
        }
    }
}
