using System.Collections.Generic;
using JacobZ.Fluss.Utils;
using Microsoft.VisualStudio.TestTools.UnitTesting;

namespace JacobZ.Fluss.Test
{
    [TestClass]
    public class ExternRarProviderTests
    {
        [TestMethod]
        public void TestCuesheet()
        {
            var str = @"REM GENRE Trance
REM DATE 2013
REM DISCID 1602FC03
REM COMMENT ""ExactAudioCopy v1.0b3""
PERFORMER ""Altanaphixx""
TITLE ""CITORIGNE""
FILE ""APXX-0202.tta"" WAVE
  TRACK 01 AUDIO
    TITLE ""oblivious waltz - 37 electro remix""
    PERFORMER ""takumiya""
    INDEX 01 00:00:00
  TRACK 02 AUDIO
    TITLE ""citorigne.gem""
    PERFORMER ""takumiya""
    INDEX 01 03:50:00
  TRACK 03 AUDIO
    TITLE ""stella -fmy. brilliance remix-""
    PERFORMER ""xaryan""
    INDEX 00 07:57:57
    INDEX 01 07:59:57
";
            Cuesheet cue = new Cuesheet();
            cue.Deserialize(str);
            var ncue = cue.Serialize();
        }
    }
}
