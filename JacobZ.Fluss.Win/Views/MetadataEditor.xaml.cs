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

namespace JacobZ.Fluss.Win.Views
{
    /// <summary>
    /// MetadataEditor.xaml 的交互逻辑
    /// </summary>
    public partial class MetadataEditor : Page
    {
        MainWindow _owner;
        public MetadataEditor(MainWindow owner)
        {
            InitializeComponent();
            DataContext = this;
            _instance = this;

            _owner = owner;
            _owner.RootPathChanged += Owner_RootPathChanged;
        }

        static MetadataEditor _instance;
        public static MetadataEditor Instance { get => _instance; }

        private void Owner_RootPathChanged(object sender, string e)
        {
        }
    }
}
