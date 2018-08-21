using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace JacobZ.Music
{
    /// <summary>
    /// 艺术家的抽象基类
    /// </summary>
    /// <remarks>
    /// 可以抽象的属性有ID、头像等等
    /// </remarks>
    public class ArtistInfo : PerformerInfo
    {
        public string Name;
        public IEnumerable<string> AliasName;
    }
}
