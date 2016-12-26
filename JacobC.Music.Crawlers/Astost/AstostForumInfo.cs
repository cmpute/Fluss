using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace JacobC.Music.Crawlers.Astost
{
    /// <summary>
    /// A坛的版块信息
    /// </summary>
    public class AstostForumInfo
    {
        /// <summary>
        /// 版块名字
        /// </summary>
        public string Name;
        /// <summary>
        /// 板块的fid
        /// </summary>
        public uint ID;
        /// <summary>
        /// 帖子数量（包含文章和回复）
        /// </summary>
        public int PostCount;
        /// <summary>
        /// 文章数量
        /// </summary>
        public int ArticleCount;

        public override string ToString()
        {
            return $"[{ID}] {Name}";
        }
    }
}
