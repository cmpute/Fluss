﻿using JacobZ.Fluss.Audio;
using System;
using System.Collections.Generic;
using System.Text;

namespace JacobZ.Fluss.Utils
{
    public static class AudioCodecFactory
    {
        public delegate void FindRequiredCodec(AudioCodecType ext);
        public static FindRequiredCodec CodecFinder { get; set; }

        public static AudioCodecType ParseCodec(string ext)
        {
            if (ext.StartsWith(".")) ext = ext.Substring(1);
            switch(ext)
            {
                case "wv": return AudioCodecType.Wavpack;
                case "tta": return AudioCodecType.TTA;
                default: return AudioCodecType.Unknown;
            }
        }

        public static IPcmCodec GetCodec(string ext)
            => GetCodec(ParseCodec(ext));

        public static IPcmCodec GetCodec(AudioCodecType type)
        {
            switch (type)
            {
                case AudioCodecType.Wavpack:
                    if (WavPack.WavPackPath == null)
                        CodecFinder(AudioCodecType.Wavpack);
                    return new WavPack();
                case AudioCodecType.TTA:
                    if (TTA.TTAPath == null)
                        CodecFinder(AudioCodecType.TTA);
                    return new TTA();
                case AudioCodecType.Unknown:
                default: return null;
            }
        }
    }
    public enum AudioCodecType
    {
        Unknown,
        Wavpack, // .wv
        TTA, // .tta
    }
}
