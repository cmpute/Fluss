using JacobZ.Fluss.Archiver;
using JacobZ.Fluss.Win.Models;
using JacobZ.Fluss.Win.Operations;
using JacobZ.Fluss.Win.Utils;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.IO;
using System.Windows;
using System.Windows.Controls;

namespace JacobZ.Fluss.Win.Views
{
    /// <summary>
    /// FileConversion.xaml 的交互逻辑
    /// </summary>
    public partial class FileConversion : Page
    {
        MainWindow _owner;

        public FileConversion(MainWindow owner)
        {
            InitializeComponent();
            DataContext = this;
            _instance = this;
            _owner = owner;;

            SourceList = new ObservableCollection<SourceItem>();
            SourceSelected = new ObservableCollection<SourceItem>();
            SourceSelected.CollectionChanged += SourceSelected_CollectionChanged;
            _owner.RootPathChanged += Owner_RootPathChanged;
        }

        static FileConversion _instance;
        public static FileConversion Instance { get => _instance; }

        public ObservableCollection<SourceItem> SourceList
        {
            get { return (ObservableCollection<SourceItem>)GetValue(SourceListProperty); }
            set { SetValue(SourceListProperty, value); }
        }
        public static readonly DependencyProperty SourceListProperty =
            DependencyProperty.Register("SourceList", typeof(ObservableCollection<SourceItem>), typeof(MainWindow), new PropertyMetadata(null));

        private void Owner_RootPathChanged(object sender, string path)
        {
            SourceList.Clear();

            var ext = Path.GetExtension(path);
            if (ext.Length == 0)
                foreach (var item in Directory.EnumerateFiles(path, "*", SearchOption.AllDirectories))
                    SourceList.Add(new SourceItem() { FilePath = item.Substring(path.Length + 1) });
            else
            {
                Archiver.IArchiver archiver;
                switch(ext)
                {
                    case ".rar":
                        archiver = new RAR(Utils.ProgramFinder.FindArchiver<RAR>());
                        break;
                    default:
                        throw new NotSupportedException("Not supported archive format!");
                }
                foreach (var item in archiver.GetContentList(path))
                    SourceList.Add(new SourceItem() { FilePath = item });
            }
        }

        public ObservableCollection<SourceItem> SourceSelected
        {
            get { return (ObservableCollection<SourceItem>)GetValue(SourceSelectedProperty); }
            set { SetValue(SourceSelectedProperty, value); }
        }
        public static readonly DependencyProperty SourceSelectedProperty =
            DependencyProperty.Register("SourceSelected", typeof(ObservableCollection<SourceItem>), typeof(MainWindow), new PropertyMetadata(null));

        private void OriginFileView_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            foreach (var item in e.RemovedItems)
                SourceSelected.Remove(item as SourceItem);
            foreach (var item in e.AddedItems)
                SourceSelected.Add(item as SourceItem);
        }

        private void SourceSelected_CollectionChanged(object sender, System.Collections.Specialized.NotifyCollectionChangedEventArgs e)
        {
            PossibleOps.ItemsSource = OperationFinder.OperationInstances.Where(
                op => SourceSelected.All(source => op.CheckUsable(source.FilePath)));
        }
    }
}
