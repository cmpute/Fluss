using JacobZ.Fluss.Utils;
using JacobZ.Fluss.Win.Models;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Collections.Specialized;
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

            SourceList = new ObservableCollection<OperationTarget>();
            SourceSelected = new ObservableCollection<OperationTarget>();
            MiddleList = new ObservableCollection<OperationTarget>();
            SourceSelected.CollectionChanged += SourceSelected_CollectionChanged;
            _owner.RootPathChanged += Owner_RootPathChanged;
        }

        static FileConversion _instance;
        public static FileConversion Instance { get => _instance; }

        private void Owner_RootPathChanged(object sender, string path)
        {
            SourceList.Clear();
            int counter = 0;
            foreach (var item in _owner.Archive.Entries.Where(item => !item.IsDirectory))
                SourceList.Add(new OperationTarget() { Archive = _owner.Archive, EntryIndex = counter++, IsSource = true });
        }

        private ObservableCollection<OperationTarget> SourceList
        {
            get { return (ObservableCollection<OperationTarget>)GetValue(SourceListProperty); }
            set { SetValue(SourceListProperty, value); }
        }
        public static readonly DependencyProperty SourceListProperty =
            DependencyProperty.Register("SourceList", typeof(ObservableCollection<OperationTarget>), typeof(FileConversion), new PropertyMetadata(null));

        private ObservableCollection<OperationTarget> SourceSelected
        {
            get { return (ObservableCollection<OperationTarget>)GetValue(SourceSelectedProperty); }
            set { SetValue(SourceSelectedProperty, value); }
        }
        public static readonly DependencyProperty SourceSelectedProperty =
            DependencyProperty.Register("SourceSelected", typeof(ObservableCollection<OperationTarget>), typeof(FileConversion), new PropertyMetadata(null));

        private ObservableCollection<OperationTarget> MiddleList
        {
            get { return (ObservableCollection<OperationTarget>)GetValue(MiddleListProperty); }
            set { SetValue(MiddleListProperty, value); }
        }
        public static readonly DependencyProperty MiddleListProperty =
            DependencyProperty.Register("MiddleList", typeof(ObservableCollection<OperationTarget>), typeof(FileConversion), new PropertyMetadata(null));

        private ObservableCollection<OperationTarget> OutputList
        {
            get { return (ObservableCollection<OperationTarget>)GetValue(OutputListProperty); }
            set { SetValue(OutputListProperty, value); }
        }
        public static readonly DependencyProperty OutputListProperty =
            DependencyProperty.Register("OutputList", typeof(ObservableCollection<OperationTarget>), typeof(FileConversion), new PropertyMetadata(null));

        private bool BatchWhenAdd
        {
            get { return (bool)GetValue(BatchWhenAddProperty); }
            set { SetValue(BatchWhenAddProperty, value); }
        }
        public static readonly DependencyProperty BatchWhenAddProperty =
            DependencyProperty.Register("BatchWhenAdd", typeof(bool), typeof(FileConversion), new PropertyMetadata(false, (dp, e) => (dp as FileConversion)?.BatchWhenAdd_PropertyChanged(dp, e)));

        private void OriginFileView_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            foreach (var item in e.RemovedItems)
                SourceSelected.Remove(item as OperationTarget);
            foreach (var item in e.AddedItems)
                SourceSelected.Add(item as OperationTarget);
            RefreshAddOpButtonState();
        }

        private void MiddleFileView_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            foreach (var item in e.RemovedItems)
                SourceSelected.Remove(item as OperationTarget);
            foreach (var item in e.AddedItems)
                SourceSelected.Add(item as OperationTarget);
            RefreshAddOpButtonState();
        }

        private void PossibleOps_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            RefreshAddOpButtonState();
        }

        private void SourceSelected_CollectionChanged(object sender, NotifyCollectionChangedEventArgs e)
        {
            if (SourceSelected.Count > 0)
                PossibleOps.ItemsSource = OperationFactory.EntryOperationTypes.Where(
                op => OperationFactory.CheckOperation(op, SourceSelected.Select(target => target.Entry).ToArray()));
            else PossibleOps.ItemsSource = null;
        }

        private void BatchWhenAdd_PropertyChanged(DependencyObject dp, DependencyPropertyChangedEventArgs e)
        {
            RefreshAddOpButtonState();
        }

        private IEnumerable<EntryCategory> CategoryValues
        {
            get { return (IEnumerable<EntryCategory>)GetValue(CategoryValuesProperty); }
            set { SetValue(CategoryValuesProperty, value); }
        }
        public static readonly DependencyProperty CategoryValuesProperty =
            DependencyProperty.Register("CategoryValues", typeof(IEnumerable<EntryCategory>), typeof(FileConversion), new PropertyMetadata(
                Enum.GetValues(typeof(EntryCategory)).Cast<EntryCategory>()));

        private void RefreshAddOpButtonState() // TODO: implement this with bindings
        {
            AddOp.IsEnabled = SourceSelected.Count > 0 && PossibleOps.SelectedItem != null;
        }

        private void AddOp_Click(object sender, RoutedEventArgs e)
        {
            
        }
    }
}
