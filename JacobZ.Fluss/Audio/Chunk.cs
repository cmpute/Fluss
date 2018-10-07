using System;
using System.Collections.Generic;
using System.IO;
using JacobZ.Fluss.Utils;

namespace JacobZ.Fluss.Audio
{
    class Chunk : Utils.Substream
    {
        string _id;

        /// <summary>
        /// Create a chunk on the top of unseekable stream
        /// </summary>
        /// <param name="source"></param>
        public Chunk(Stream source) : this(source, BitConverter.IsLittleEndian) { }
        public Chunk(Stream source, bool littleEndian) : base(source)
        {
            BinaryReader br = new BinaryReader(source);
            _id = string.Join(string.Empty, br.ReadChars(4));
            _length = br.ReadUInt32(littleEndian);
            _start = -1;
        }
        public Chunk(Stream source, long startPos) : this(source, startPos, BitConverter.IsLittleEndian) { }
        public Chunk(Stream source, long startPos, bool littleEndian) : base(source)
        {
            // Lazy load
            var opos = source.Position;
            if (startPos != opos)
                source.Seek(startPos, SeekOrigin.Begin);

            BinaryReader br = new BinaryReader(source);
            _id = string.Join(string.Empty, br.ReadChars(4));
            _length = br.ReadUInt32(littleEndian);
            _start = startPos + 8;

            if (startPos != opos)
                source.Seek(opos, SeekOrigin.Begin);
        }
        public Chunk(string id, byte[] data) : base(new MemoryStream(data), 0, data.Length)
        {
            _id = id;
        }

        public string Id => _id.TrimEnd(' ');
    }
}
