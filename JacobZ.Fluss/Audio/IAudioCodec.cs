using System.IO;

namespace JacobZ.Fluss.Audio
{
    public interface IPcmCodec
    {
        /// <summary>
        /// Encode audio into file
        /// </summary>
        void Encode(string outputFile, Stream input);

        /// <summary>
        /// Decode audio from file
        /// </summary>
        Stream Decode(string inputFile);
    }
}
