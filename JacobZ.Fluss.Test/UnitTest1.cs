using System.Collections.Generic;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace JacobZ.Fluss.Test
{
    [TestClass]
    public class ExternRarProviderTests
    {
        JacobZ.Fluss.Archiver.ExternRarProvider extractor;

        [TestInitialize]
        public void Prepare()
        {
            extractor = new Archiver.ExternRarProvider("E:/@Temp/Rar.exe");
        }
    }
}
