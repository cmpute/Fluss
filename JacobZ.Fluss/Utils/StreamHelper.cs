using System;
using System.Collections.Generic;
using System.IO;
using System.Diagnostics;
using System.Text;

namespace JacobZ.Fluss.Utils
{
    static class StreamHelper
    {
        private static byte[] ReadBytesR(BinaryReader reader, int count, bool reverse)
        {
            byte[] data = reader.ReadBytes(count);
            if (reverse)
                for (int i = 0; i < count / 2; i++)
                {
                    byte temp = data[i];
                    data[i] = data[count - 1 - i];
                    data[count - 1 - i] = temp;
                }
            return data;
        }

        public static short ReadInt16(this BinaryReader reader, bool isLittleEndian)
        {
            byte[] buffer = ReadBytesR(reader, 2, isLittleEndian != BitConverter.IsLittleEndian);
            return BitConverter.ToInt16(buffer, 0);
        }

        public static int ReadInt32(this BinaryReader reader, bool isLittleEndian)
        {
            byte[] buffer = ReadBytesR(reader, 4, isLittleEndian != BitConverter.IsLittleEndian);
            return BitConverter.ToInt32(buffer, 0);
        }

        public static long ReadInt64(this BinaryReader reader, bool isLittleEndian)
        {
            byte[] buffer = ReadBytesR(reader, 8, isLittleEndian != BitConverter.IsLittleEndian);
            return BitConverter.ToInt64(buffer, 0);
        }

        public static ushort ReadUInt16(this BinaryReader reader, bool isLittleEndian)
        {
            byte[] buffer = ReadBytesR(reader, 2, isLittleEndian != BitConverter.IsLittleEndian);
            return BitConverter.ToUInt16(buffer, 0);
        }

        public static uint ReadUInt32(this BinaryReader reader, bool isLittleEndian)
        {
            byte[] buffer = ReadBytesR(reader, 4, isLittleEndian != BitConverter.IsLittleEndian);
            return BitConverter.ToUInt32(buffer, 0);
        }

        public static ulong ReadUInt64(this BinaryReader reader, bool isLittleEndian)
        {
            byte[] buffer = ReadBytesR(reader, 8, isLittleEndian != BitConverter.IsLittleEndian);
            return BitConverter.ToUInt64(buffer, 0);
        }
    }

    public class Substream : Stream
    {
        protected long _start, _length;
        protected Substream(Stream stream) { BaseStream = stream; }
        public Substream(Stream stream, long offset)
        {
            BaseStream = stream;
            _start = offset;
            _length = stream.Length - _start;
        }
        public Substream(Stream stream, long offset, long length)
        {
            BaseStream = stream;
            _start = offset;
            _length = stream.Length - _start;
        }

        public Stream BaseStream { get; protected set; }

        public override bool CanRead => BaseStream.CanRead;
        public override bool CanSeek => BaseStream.CanSeek;
        public override bool CanWrite => BaseStream.CanWrite;

        public override long Length => _length;
        public override long Position
        {
            get => BaseStream.Position - _start;
            set => BaseStream.Position = value + _start;
        }
        
        public override void Flush() => BaseStream.Flush();
        public override int Read(byte[] buffer, int offset, int count) => BaseStream.Read(buffer, offset, count);
        public override long Seek(long offset, SeekOrigin origin)
        {
            long result = 0;
            switch (origin)
            {
                case SeekOrigin.Begin:
                    result = BaseStream.Seek(_start + offset, origin);
                    break;
                case SeekOrigin.Current:
                    result = BaseStream.Seek(offset, origin);
                    break;
                case SeekOrigin.End:
                    result = BaseStream.Seek(_start + _length + offset, SeekOrigin.Begin);
                    break;
            }
            return result - _start;
        }
        public override void SetLength(long value)
        {
            BaseStream.SetLength(value - _length + BaseStream.Length);
        }
        public override void Write(byte[] buffer, int offset, int count) =>BaseStream.Write(buffer, offset, count);
    }

    public enum ProcessPipeType
    {
        Stdin, Stdout, Stderr
    }

    public class ProcessStream : Stream
    {
        public Stream BaseStream { get; protected set; }
        public Process AssociatedProcess { get; protected set; }

        public ProcessStream(Process process, ProcessPipeType pipe = ProcessPipeType.Stdout)
        {
            AssociatedProcess = process;
            switch(pipe)
            {
                case ProcessPipeType.Stdout:
                    BaseStream = process.StandardOutput.BaseStream;
                    break;
                case ProcessPipeType.Stdin:
                    BaseStream = process.StandardInput.BaseStream;
                    break;
                case ProcessPipeType.Stderr:
                    BaseStream = process.StandardError.BaseStream;
                    break;
            }
        }
        protected override void Dispose(bool disposing)
        {
            base.Dispose(disposing);
            if (disposing) AssociatedProcess.EnsureExit();
        }

        public override bool CanRead => BaseStream.CanRead;
        public override bool CanSeek => BaseStream.CanSeek;
        public override bool CanWrite => BaseStream.CanWrite;
        public override long Length => BaseStream.Length;
        public override long Position
        {
            get => BaseStream.Position;
            set => BaseStream.Position = value;
        }
        public override void Flush() => BaseStream.Flush();
        public override int Read(byte[] buffer, int offset, int count) => BaseStream.Read(buffer, offset, count);
        public override long Seek(long offset, SeekOrigin origin) => BaseStream.Seek(offset, origin);
        public override void SetLength(long value) => BaseStream.SetLength(value);
        public override void Write(byte[] buffer, int offset, int count) => BaseStream.Write(buffer, offset, count);
    }
}
