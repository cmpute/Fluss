using Microsoft.WindowsAPICodePack.Dialogs;
using System;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;
using SharpCompress.Archives;
using JacobZ.Fluss.Utils;

namespace JacobZ.Fluss.Win
{
    /// <summary>
    /// MainWindow.xaml 的交互逻辑
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();

            new Views.FileConversion(this);
            new Views.MetaInfo();
        }

        private void Window_Loaded(object sender, RoutedEventArgs e)
        {
            this.MainFrame.Navigate(Views.FileConversion.Instance);
        }

        private void ListBox_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            var selected = e.AddedItems[0];
            if (selected == (sender as ListBox).Items[0])
                MainFrame.Navigate(Views.FileConversion.Instance);
            else if (selected == (sender as ListBox).Items[1])
                MainFrame.Navigate(Views.MetaInfo.Instance);
        }

        private void BrowseDirectoryButton_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new CommonOpenFileDialog()
            {
                IsFolderPicker = true,
                EnsurePathExists = true
            };
            var result = dialog.ShowDialog(new WindowInteropHelper(this).Handle);
            if (result != CommonFileDialogResult.Ok) return;

            RootPath.Text = dialog.FileName;
        }

        private void BrowseFileButton_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new CommonOpenFileDialog();
            dialog.Filters.Add(new CommonFileDialogFilter("RAR archive", ".rar"));
            var result = dialog.ShowDialog(new WindowInteropHelper(this).Handle);
            if (result != CommonFileDialogResult.Ok) return;

            RootPath.Text = dialog.FileName;
        }

        public event EventHandler<string> RootPathChanged;
        public MusicArchive Archive { get; set; }

        private void RootPath_TextChanged(object sender, TextChangedEventArgs e)
        {
            // Update archive object
            IArchive archive;
            var ext = Path.GetExtension(RootPath.Text);
            if (ext.Length == 0)
                archive = new DirectoryArchive(RootPath.Text);
            else
            {
                switch (ext)
                {
                    case ".rar":
                        archive = SharpCompress.Archives.Rar.RarArchive.Open(new FileInfo(RootPath.Text));
                        break;
                    case ".zip":
                        archive = SharpCompress.Archives.Zip.ZipArchive.Open(new FileInfo(RootPath.Text));
                        break;
                    default:
                        throw new NotSupportedException("Not supported archive format!");
                }
            }
            Archive = new MusicArchive(archive);

            // Notify pages
            RootPathChanged.Invoke(this, RootPath.Text);
        }

        private void BrowseOutput_Click(object sender, RoutedEventArgs e)
        {
            var dialog = new CommonOpenFileDialog()
            {
                IsFolderPicker = true
            };
            var result = dialog.ShowDialog(new WindowInteropHelper(this).Handle);
            if (result != CommonFileDialogResult.Ok) return;

            OutputPath.Text = dialog.FileName;
        }
    }
}
