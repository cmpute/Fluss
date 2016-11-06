using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;
using TrackArtist = System.Tuple<JacobC.Music.ArtistInfo, JacobC.Music.ArtistChara>;

namespace JacobC.Music
{
    public class AlbumInfo : InfoBase
    {
        public string Name;

        /// <summary>
        /// 专辑属性
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
        /// 专辑艺术家
        /// </summary>
        public PerformerInfo Performer;

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
        /// 相关网站
        /// </summary>
        public IEnumerable<Uri> RelateWebsite;

        /// <summary>
        /// 专辑编号/番号
        /// </summary>
        public string Catalog;

        public IList<DiskInfo> Disks;
    }

    public struct DiskInfo
    {
        public uint DiskNumber;
        public IList<TrackInfo> TrackList;
    }

    public class TrackInfo
    {
        public uint TrackNumber;
        public string Name;
        public IEnumerable<TrackArtist> Artists;
    }
}
