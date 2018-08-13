using System;
using System.Collections.Generic;
using System.Text;

namespace JacobZ.Fluss.Encoder
{
    public interface IAudioEncoder
    {
        /// <summary>
        /// 编码音频文件
        /// </summary>
        /// <param name="wavPath">WAV文件位置</param>
        void Encode(string wavPath);

        /// <summary>
        /// 解码音频文件
        /// </summary>
        /// <param name="audioPath">音频文件位置</param>
        void Decode(string audioPath);

        void ReadTags(string audioPath);

        void WriteTags(string audioPath);
    }
}
