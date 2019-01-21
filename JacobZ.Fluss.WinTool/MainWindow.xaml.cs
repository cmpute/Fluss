using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Documents;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Imaging;
using System.Windows.Navigation;
using System.Windows.Shapes;
using JacobZ.Fluss.WinTool.Pages;

namespace JacobZ.Fluss.WinTool
{
    /// <summary>
    /// MainWindow.xaml 的交互逻辑
    /// </summary>
    public partial class MainWindow : Window
    {
        public MainWindow()
        {
            InitializeComponent();
        }

        private void Window_DragEnter(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                var files = (string[])e.Data.GetData(DataFormats.FileDrop);
                if (files != null && files.Length == 1)
                {
                    e.Effects = DragDropEffects.Link;
                    return;
                }
            }
            e.Effects = DragDropEffects.None;
            e.Handled = true;
        }

        private void Window_Drop(object sender, DragEventArgs e)
        {
            if (!e.Data.GetDataPresent(DataFormats.FileDrop)) return;
            var files = (string[])e.Data.GetData(DataFormats.FileDrop);
            if (files.Length > 1) MessageBox.Show("Please drop only one file here");

            if (Directory.Exists(files[0]))
            {
                MainFrame.Navigate(new ArchiveEditor(files[0]));
                MainTip.Visibility = Visibility.Hidden;
            }
            else if (ImageMagick.MagickNET.GetFormatInformation(files[0]) != null)
            {
                MainFrame.Navigate(new ImageEditor(files[0]));
                MainTip.Visibility = Visibility.Hidden;
            }
        }
    }
}
