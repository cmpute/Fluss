﻿using System;
using System.IO;
using System.Collections.Generic;
using TextEncoding = System.Text.Encoding;
using JacobZ.Fluss.Utils;
using System.Threading;
using System.Threading.Tasks;

namespace JacobZ.Fluss.Audio
{
    public enum PcmEncodingType
    {
        RAW,
        RIFF,
        AIFF,
        RF64,
        W64
    };

    public class PcmStream : Substream
    {
        const uint WAVE_FORMAT_PCM = 0x0001;

        public WaveFormat Format { get; private set; }
        public PcmEncodingType Encoding { get; private set; }

        public PcmStream(Stream stream, PcmEncodingType encoding) : base(stream)
        {
            Encoding = encoding;
            Format = new WaveFormat();
            switch (Encoding)
            {
                default:
                case PcmEncodingType.RAW:
                    throw new ArgumentException("Do not use this constructor to make a raw data stream!");
                case PcmEncodingType.RIFF:
                    var chunk = new Chunk(stream, true);
                    if (chunk.Id != "RIFF") throw new FormatException("The stream format is not valid RIFF!");

                    BinaryReader chunkbr = new BinaryReader(chunk);
                    if (string.Join(string.Empty, chunkbr.ReadChars(4)) != "WAVE")
                        throw new FormatException("The stream format is not RIFF!");
                    
                    var fmtchunk = new Chunk(chunk, true);
                    if (fmtchunk.Id != "fmt") throw new FormatException("The stream format is not valid RIFF!");
                    BinaryReader fmtbr = new BinaryReader(fmtchunk);

                    // 编码解码用的原始流不支持压缩格式
                    // 完整Wave格式列表参见 https://github.com/naudio/NAudio/blob/master/NAudio/Wave/WaveFormats/WaveFormatEncoding.cs
                    var audiofmt = fmtbr.ReadUInt16(true);
                    if (audiofmt != 1) throw new NotSupportedException("Wave format with data format other than PCM is not supported!");

                    Format.Channels = fmtbr.ReadUInt16(true);
                    Format.SampleRate = fmtbr.ReadUInt32(true);
                    uint birate = fmtbr.ReadUInt32(true);
                    Format.BlockAlign = fmtbr.ReadUInt16(true);
                    Format.SampleWidth = fmtbr.ReadUInt16(true);

                    var datachunk = new Chunk(chunk, true);
                    BaseStream = datachunk;
                    _start = 0;
                    _length = datachunk.Length;

                    break;
            }
        }
        public PcmStream(Stream stream, WaveFormat format) : base(stream)
        {
            Format = format;
            Encoding = PcmEncodingType.RAW;
        }

        public void CopyHeaderTo(Stream destination)
        {
            switch(Encoding)
            {
                default:
                case PcmEncodingType.RAW:
                    break;
                case PcmEncodingType.RIFF:
                    BinaryWriter bw = new BinaryWriter(destination);
                    bw.Write(new char[] { 'R', 'I', 'F', 'F' });
                    bw.Write((uint)(BaseStream.Length + 36), true);
                    bw.Write(new char[] { 'W', 'A', 'V', 'E', 'f', 'm', 't', ' ' });
                    bw.Write((uint)16, true);
                    bw.Write((ushort)WAVE_FORMAT_PCM, true);
                    bw.Write((ushort)Format.Channels, true);
                    bw.Write((uint)Format.SampleRate, true);
                    bw.Write((uint)(Format.SampleRate * Format.SampleWidth * Format.Channels / 8), true);
                    bw.Write((ushort)Format.BlockAlign, true);
                    bw.Write((ushort)Format.SampleWidth, true);
                    bw.Write(new char[] { 'd', 'a', 't', 'a' });
                    bw.Write((uint)BaseStream.Length, true);
                    break;
            }
        }
    }
}
