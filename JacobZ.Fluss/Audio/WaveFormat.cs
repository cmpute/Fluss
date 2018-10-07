using System;
using System.Collections.Generic;
using System.Text;

namespace JacobZ.Fluss.Audio
{
    public class WaveFormat
    {
        /// <summary> Sample Frequency </summary>
        public uint SampleWidth { get; set; }
        /// <summary> Number of channels </summary>
        public uint Channels { get; set; }
        /// <summary> Bits per sample </summary>
        public uint SampleRate { get; set; }
        /// <summary> Block size of data </summary>
        /// <remarks>
        /// This should be <see cref="WaveFormat.Channels"/> *
        /// <see cref="WaveFormat.SampleWidth"/> / 8
        /// </remarks>
        public uint BlockAlign { get; set; }

        /// <summary> Bits per second </summary>
        public uint Bitrate => SampleWidth * Channels * SampleRate;
    }
}
