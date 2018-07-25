using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using TrackArtist = System.Tuple<JacobZ.Music.ArtistInfo, JacobZ.Music.ArtistChara>;

namespace JacobZ.Music
{
    public class AlbumInfo : InfoBase
    {
        /// <summary>
        /// 专辑名称
        /// </summary>
        public string Name;

        /// <summary>
        /// 专辑属性 TODO:完善专辑属性的分类
        /// </summary>
        public string Attribute;

        /// <summary>
        /// 专辑版本
        /// </summary>
        /// <remarks>如初回限定版、期间生产限定版等</remarks>
        public string Edition;

        /// <summary>
        /// 专辑的压制信息
        /// </summary>
        public RipInfo Rip;

        /// <summary>
        /// 专辑表演者（主要指歌手或组合）
        /// </summary>
        public PerformerInfo Performer;

        /// <summary>
        /// 专辑其他艺术家
        /// </summary>
        public IEnumerable<TrackArtist> Artists;

        /// <summary>
        /// 专辑发行公司
        /// </summary>
        public string Publisher;

        /// <summary>
        /// 发售展会（同人专辑）
        /// </summary>
        public string Event;

        /// <summary>
        /// 发售日期 [YYMMDD]
        /// </summary>
        public string Date;

        /// <summary>
        /// 专辑编号/番号
        /// </summary>
        public string Catalog;

        /// <summary>
        /// 专辑所含的Disc列表
        /// </summary>
        public IList<DiscInfo> Discs;

        /// <summary>
        /// 专辑附件，包括DVD、BK、特典等等
        /// </summary>
        public IEnumerable<InfoBase> Attachments;
    }

    public struct DiscInfo
    {
        /// <summary>
        /// 部分专辑每一张碟子都是有标题的
        /// </summary>
        public string DiscName;
        /// <summary>
        /// 碟片编号
        /// </summary>
        /// <remarks>
        /// DiscNumber=0代表该Disc是专辑唯一的碟片
        /// </remarks>
        public uint DiscNumber;
        /// <summary>
        /// 碟片所含音轨列表
        /// </summary>
        public IList<TrackInfo> TrackList;
    }

    public class TrackInfo
    {
        public uint TrackNumber;
        public string Name;
        public IEnumerable<TrackArtist> Artists;
    }
}
