using Microsoft.WindowsAPICodePack.Dialogs;
using System;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Interop;

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

        private void RootPath_TextChanged(object sender, TextChangedEventArgs e)
        {
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
