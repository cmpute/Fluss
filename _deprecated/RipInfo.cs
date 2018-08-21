using System;
using System.Collections.Generic;
using System.Linq;
using System.Security.Policy;
using System.Text;
using System.Threading.Tasks;

namespace JacobZ.Music
{
    public class RipInfo : InfoBase
    {
        /// <summary>
        /// 压制工具列表
        /// </summary>
        public enum RipTool
        {
            /// <summary>
            /// Exact Audio Copy
            /// </summary>
            EAC,

            /// <summary>
            /// X Lossless Decoder
            /// </summary>
            XLD,

            /// <summary>
            /// ImgBurn
            /// </summary>
            ImgBurn,

            /// <summary>
            /// 其他
            /// </summary>
            Others
        }

        /// <summary>
        /// 压制工具
        /// </summary>
        public RipTool Tool;

        /// <summary>
        /// 压制工具版本
        /// </summary>
        public string ToolVersion;

        /// <summary>
        /// 压制来源硬件的类型列表
        /// </summary>
        public enum HardwareType
        {
            CD,
            DVD,

            /// <summary>
            /// 蓝光碟
            /// </summary>
            Blueray,

            /// <summary>
            /// 直播流录制（含TVRIP）
            /// </summary>
            LiveStream,

            /// <summary>
            /// 网络配信购买，即购买的是电子版
            /// </summary>
            OnlineShop
        }

        /// <summary>
        /// 压制来源硬件
        /// </summary>
        public HardwareType Hardware;

        /// <summary>
        /// 压制者ID/自抓者ID
        /// </summary>
        /// <remarks>
        /// 为空时代表来源不明
        /// </remarks>
        public string RipperId;

        /// <summary>
        /// 判断是否是自抓
        /// </summary>
        public bool IsSelfRip => RipperId != null;

        /// <summary>
        /// 是否可以转载
        /// </summary>
        public bool Distributable;

        /// <summary>
        /// 下载来源网站
        /// </summary>
        public Uri SourceWebsite;
    }
}
