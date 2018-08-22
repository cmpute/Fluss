using System.IO;

namespace JacobZ.Fluss.AudioCodec
{
    public interface IAudioCodec
    {
        /// <summary>
        /// 编码音频文件
        /// </summary>
        void Encode(Stream input, string outputFile);

        /// <summary>
        /// 解码音频文件
        /// </summary>
        void Decode(Stream output, string inputFile);

        void ReadTags(string input);

        void WriteTags(string output);
    }
}
