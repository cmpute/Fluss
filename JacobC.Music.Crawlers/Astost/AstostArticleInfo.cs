using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers.Astost
{
    /// <summary>
    /// A坛的文章信息
    /// </summary>
    public class AstostArticleInfo
    {
        /// <summary>
        /// 文章的tid
        /// </summary>
        public uint ThreadID { get; set; }
        /// <summary>
        /// 文章标题
        /// </summary>
        public string Title { get; set; }
        /// <summary>
        /// 作者id
        /// </summary>
        public uint UserID { get; set; }
        /// <summary>
        /// 作者的用户名
        /// </summary>
        public string UserName { get; set; }
        /// <summary>
        /// 文章是否被置顶
        /// </summary>
        public bool Pinned { get; set; } = false;
        /// <summary>
        /// 文章被发表的日期
        /// </summary>
        public string PostDate { get; set; }
        /// <summary>
        /// 文章最后被更新的日期
        /// </summary>
        public string LastUpdateDate { get { throw new NotImplementedException(); } }
        /// <summary>
        /// 文章分类
        /// </summary>
        public string Category { get { throw new NotImplementedException(); } }

        public override string ToString()
        {
            return Pinned ? $"[Pinned][{ThreadID}]:{Title}" : $"[{ThreadID}]:{Title}";
        }
    }
}
