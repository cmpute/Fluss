using System;
using System.IO;
using System.Collections.Generic;
using TextEncoding = System.Text.Encoding;
using JacobZ.Fluss.Utils;
using System.Threading;
using System.Threading.Tasks;

namespace JacobZ.Fluss.Audio
{
    // Only support RIFF format, transform input format before using this class
    // TODO: maybe support RF64?
    public class PcmStream : Substream
    {
        const uint WAVE_FORMAT_PCM = 0x0001;

        public WaveFormat Format { get; private set; }

        public PcmStream(Stream stream) : base(stream)
        {
            Format = new WaveFormat();
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
            if (audiofmt != WAVE_FORMAT_PCM) throw new NotSupportedException("Wave format with data format other than PCM is not supported!");

            Format.Channels = fmtbr.ReadUInt16(true);
            Format.SampleRate = fmtbr.ReadUInt32(true);
            uint birate = fmtbr.ReadUInt32(true);
            Format.BlockAlign = fmtbr.ReadUInt16(true);
            Format.SampleWidth = fmtbr.ReadUInt16(true);

            var datachunk = new Chunk(chunk, true);
            BaseStream = datachunk;
            _start = 0;
            _length = datachunk.Length;

        }
        public PcmStream(Stream stream, WaveFormat format) : base(stream)
        {
            Format = format;
        }

        public void CopyHeaderTo(Stream destination)
        {
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
        }

        public TimeSpan TimePosition { get => throw new NotImplementedException(); }
        public TimeSpan Duration { get => throw new NotImplementedException(); }
    }
}
