using System;
using System.Collections.Generic;
using System.Text;

namespace JacobZ.Fluss.Audio
{
    public static class CodecFactory
    {
        public delegate void FindRequiredCodec(CodecType ext);
        public static FindRequiredCodec CodecFinder { get; set; }

        public static CodecType ParseCodec(string ext)
        {
            if (ext.StartsWith(".")) ext = ext.Substring(1);
            switch(ext)
            {
                case "wv": return CodecType.Wavpack;
                case "tta": return CodecType.TTA;
                default: return CodecType.Unknown;
            }
        }

        public static IPcmCodec GetCodec(string ext)
            => GetCodec(ParseCodec(ext));

        public static IPcmCodec GetCodec(CodecType type)
        {
            switch (type)
            {
                case CodecType.Wavpack:
                    if (WavPack.WavPackPath == null)
                        CodecFinder(CodecType.Wavpack);
                    return new WavPack();
                case CodecType.TTA:
                    if (TTA.TTAPath == null)
                        CodecFinder(CodecType.TTA);
                    return new TTA();
                case CodecType.Unknown:
                default: return null;
            }
        }
    }
    public enum CodecType
    {
        Unknown,
        Wavpack, // .wv
        TTA, // .tta
    }
}
