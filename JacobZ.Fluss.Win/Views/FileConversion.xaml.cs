using JacobZ.Fluss.Win.Models;
using JacobZ.Fluss.Win.Utils;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.IO;
using System.Windows;
using System.Windows.Controls;
using SharpCompress.Common;
using SharpCompress.Archives;

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
            _owner = owner;

            SourceList = new ObservableCollection<SourceItem>();
            SourceSelected = new ObservableCollection<SourceItem>();
            SourceSelected.CollectionChanged += SourceSelected_CollectionChanged;
            _owner.RootPathChanged += Owner_RootPathChanged;
        }

        static FileConversion _instance;
        public static FileConversion Instance { get => _instance; }

        private ObservableCollection<SourceItem> SourceList
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
                IArchive archive;
                switch(ext)
                {
                    case ".rar":
                        archive = SharpCompress.Archives.Rar.RarArchive.Open(new FileInfo(path));
                        break;
                    default:
                        throw new NotSupportedException("Not supported archive format!");
                }
                foreach (var item in archive.Entries.Where(item => !item.IsDirectory))
                    SourceList.Add(new SourceItem() { FilePath = item.Key });
            }
        }

        private ObservableCollection<SourceItem> SourceSelected
        {
            get { return (ObservableCollection<SourceItem>)GetValue(SourceSelectedProperty); }
            set { SetValue(SourceSelectedProperty, value); }
        }
        public static readonly DependencyProperty SourceSelectedProperty =
            DependencyProperty.Register("SourceSelected", typeof(ObservableCollection<SourceItem>), typeof(MainWindow), new PropertyMetadata(null));

        private ObservableCollection<OutputItem> OutputList
        {
            get { return (ObservableCollection<OutputItem>)GetValue(OutputListProperty); }
            set { SetValue(OutputListProperty, value); }
        }
        public static readonly DependencyProperty OutputListProperty =
            DependencyProperty.Register("OutputList", typeof(ObservableCollection<OutputItem>), typeof(MainWindow), new PropertyMetadata(null));

        private void OriginFileView_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            foreach (var item in e.RemovedItems)
                SourceSelected.Remove(item as SourceItem);
            foreach (var item in e.AddedItems)
                SourceSelected.Add(item as SourceItem);
            RefreshAddOpButtonState();
        }

        private void PossibleOps_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            RefreshAddOpButtonState();
        }

        private void SourceSelected_CollectionChanged(object sender, System.Collections.Specialized.NotifyCollectionChangedEventArgs e)
        {
            // TODO: Fix operations
            // PossibleOps.ItemsSource = OperationFinder.OperationInstances.Where(
            //     op => SourceSelected.All(source => op.CheckUsable(source.FilePath)));
        }

        private void RefreshAddOpButtonState()
        {
            AddOp.IsEnabled = SourceSelected.Count > 0 && PossibleOps.SelectedItem != null;
        }

        private void AddOp_Click(object sender, RoutedEventArgs e)
        {
            
        }
    }
}
