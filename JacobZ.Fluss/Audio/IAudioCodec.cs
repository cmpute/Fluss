using System.IO;

namespace JacobZ.Fluss.Audio
{
    public interface IPcmCodec
    {
        /// <summary>
        /// Encode audio into file
        /// </summary>
        void Encode(string outputFile, Stream input, PcmEncodingType type);

        /// <summary>
        /// Decode audio from file
        /// </summary>
        Stream Decode(string inputFile, PcmEncodingType type);

        void ReadTags(string input);

        void WriteTags(string output);
    }
}
