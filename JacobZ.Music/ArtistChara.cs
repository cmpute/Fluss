using System;

namespace JacobZ.Music
{
    /// <summary>
    /// 标志艺术家在条目中的角色
    /// </summary>
    [Flags]
    public enum ArtistChara
    {
        Others=0,
        /// <summary>
        /// 表演者（包括Vocalist、Arranger和Composer）
        /// </summary>
        Performer=0x01,
        /// <summary>
        /// 歌手
        /// </summary>
        Vocalist=0x03,
        /// <summary>
        /// 编曲家
        /// </summary>
        Arranger=0x09,
        /// <summary>
        /// 作曲家
        /// </summary>
        Composer=0x11,
        /// <summary>
        /// 作词家
        /// </summary>
        Lyrist=0x20,
        /// <summary>
        /// Master
        /// </summary>
        Mastering=0x40,
        /// <summary>
        /// 混响师
        /// </summary>
        Mixing=0x80
    }
}