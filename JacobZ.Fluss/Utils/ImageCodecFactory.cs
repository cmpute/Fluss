using System;
using System.Collections.Generic;
using System.Text;
using ImageMagick;

namespace JacobZ.Fluss.Utils
{
    public static class ImageCodecFactory
    {
        public static ImageCodecType ParseCodec(string ext)
        {
            if (ext.StartsWith(".")) ext = ext.Substring(1);
            switch (ext)
            {
                case "bmp": return ImageCodecType.BMP;
                case "jpg": return ImageCodecType.JPG;
                case "tiff": return ImageCodecType.TIFF;
                case "png": return ImageCodecType.PNG;
                default: return ImageCodecType.Unknown;
            }
        }
    }

    public enum ImageCodecType
    {
        Unknown,
        BMP = MagickFormat.Bmp,
        JPG = MagickFormat.Jpeg,
        TIFF = MagickFormat.Tiff,
        PNG = MagickFormat.Png00,
    }
}
