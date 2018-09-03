using System;
using System.Linq;
using System.IO;

namespace JacobZ.Fluss.Win.Operations
{
    static class TargetClassifier
    {
        private const string Folder_Booklet = "Booklet";
        private const string Folder_CompactDisc = "CD";
        private const string Folder_DigitalVersatileDisc = "DVD";
        private const string Folder_BluerayDisc = "BD";
        private const string Folder_OnlineContents = "Online";
        private const string Folder_SpecialContents = "Special"; // 特典

        public readonly static string[] TargetFolders = {
            Folder_Booklet,
            Folder_CompactDisc,
            Folder_DigitalVersatileDisc,
            Folder_BluerayDisc,
            Folder_OnlineContents,
            Folder_SpecialContents
        };

        public static string GuessFolder(string file)
        {
            if (AudioConverter.SupportedFormats.Contains(Path.GetExtension(file)))
                return Folder_CompactDisc;
            else return Folder_SpecialContents;
        }
    }
}
