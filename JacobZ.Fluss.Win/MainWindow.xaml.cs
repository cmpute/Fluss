using System;
using System.Collections.Generic;
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

            new Views.FileConversion();
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
    }
}
