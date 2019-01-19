using JacobZ.Fluss.Operation;
using JacobZ.Fluss.Utils;
using JacobZ.Fluss.Win.Models;
using JacobZ.Fluss.Win.Utils;
using SharpCompress.Archives;
using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Collections.Specialized;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Input;

namespace JacobZ.Fluss.Win.Views
{
    /// <summary>
    /// FileConversion.xaml 的交互逻辑
    /// </summary>
    public partial class FileConversion : Page
    {
        MainWindow _owner;
        bool _ctrl_pressed = false;
        OperationTarget _focus_target = null;

        public FileConversion(MainWindow owner)
        {
            InitializeComponent();
            DataContext = this;
            _instance = this;

            _owner = owner;
            _owner.RootPathChanged += Owner_RootPathChanged;
            SourceSelected = new ObservableCollection<OperationTarget>();
            OutputSelected = new ObservableCollection<OperationTarget>();
            SourceSelected.CollectionChanged += SourceSelected_CollectionChanged;
            OutputSelected.CollectionChanged += OutputSelected_CollectionChanged;

            // Using program finder
            AudioCodecFactory.CodecFinder = ProgramFinder.FindCodec;
        }

        static FileConversion _instance;
        public static FileConversion Instance { get => _instance; }

        private void Owner_RootPathChanged(object sender, string path)
        {
            SourceList.Clear();
            foreach (var item in _owner.Archive.Entries.Where(item => !item.IsDirectory))
                SourceList.Add(new OperationTarget()
                {
                    Entry = item,
                    Kind = OperationTargetKind.Input
                });
        }

        Dictionary<Type, string> OperationNames => new Dictionary<Type, string>
        {
            { typeof(PassThrough), nameof(PassThrough) },
            { typeof(FixCuesheet), nameof(FixCuesheet) },
            { typeof(FixEncoding), nameof(FixEncoding) },
            { typeof(RecodeAudio), nameof(RecodeAudio) },
            { typeof(EmbedMetadata), nameof(EmbedMetadata) },
            { typeof(RecodeImage), nameof(RecodeImage) },
            { typeof(CutCover), nameof(CutCover) }
        };
        private Tuple<IArchiveEntryOperation, string> GetOperationTuple(IArchiveEntryOperation op)
        {
            return new Tuple<IArchiveEntryOperation, string>(op, OperationNames[op.GetType()]);
        }

        #region Property and List change events

        private ObservableCollection<OperationTarget> SourceList
        {
            get { return (ObservableCollection<OperationTarget>)GetValue(SourceListProperty); }
            set { SetValue(SourceListProperty, value); }
        }
        public static readonly DependencyProperty SourceListProperty =
            DependencyProperty.Register("SourceList", typeof(ObservableCollection<OperationTarget>), typeof(FileConversion), new PropertyMetadata(new ObservableCollection<OperationTarget>()));

        private ObservableCollection<OperationTarget> SourceSelected;

        private ObservableCollection<OperationTarget> MiddleList
        {
            get { return (ObservableCollection<OperationTarget>)GetValue(MiddleListProperty); }
            set { SetValue(MiddleListProperty, value); }
        }
        public static readonly DependencyProperty MiddleListProperty =
            DependencyProperty.Register("MiddleList", typeof(ObservableCollection<OperationTarget>), typeof(FileConversion), new PropertyMetadata(new ObservableCollection<OperationTarget>()));

        private ObservableCollection<OperationTarget> OutputList
        {
            get { return (ObservableCollection<OperationTarget>)GetValue(OutputListProperty); }
            set { SetValue(OutputListProperty, value); }
        }
        public static readonly DependencyProperty OutputListProperty =
            DependencyProperty.Register("OutputList", typeof(ObservableCollection<OperationTarget>), typeof(FileConversion), new PropertyMetadata(new ObservableCollection<OperationTarget>()));

        private ObservableCollection<OperationTarget> OutputSelected;

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

            RefreshButtonState();
            _focus_target = null;
            if (!_ctrl_pressed && e.AddedItems.Count > 0)
            {
                MiddleFileView.SelectedItems.Clear();
                ConvertedFileView.SelectedItems.Clear();
            }
        }

        private void MiddleFileView_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            foreach (var item in e.RemovedItems)
            {
                SourceSelected.Remove(item as OperationTarget);
                OutputSelected.Remove(item as OperationTarget);
            }
            foreach (var item in e.AddedItems)
            {
                SourceSelected.Add(item as OperationTarget);
                OutputSelected.Add(item as OperationTarget);
            }

            RefreshButtonState();
            _focus_target = null;
            if (!_ctrl_pressed && e.AddedItems.Count > 0)
            {
                OriginFileView.SelectedItems.Clear();
                ConvertedFileView.SelectedItems.Clear();
            }
        }

        private void ConvertedFileView_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            foreach (var item in e.RemovedItems)
                OutputSelected.Remove(item as OperationTarget);
            foreach (var item in e.AddedItems)
                OutputSelected.Add(item as OperationTarget);

            RefreshButtonState();
            _focus_target = null;
            if (!_ctrl_pressed && e.AddedItems.Count > 0)
            {
                OriginFileView.SelectedItems.Clear();
                MiddleFileView.SelectedItems.Clear();
            }
        }

        private void PossibleOps_SelectionChanged(object sender, SelectionChangedEventArgs e)
        {
            RefreshButtonState();
        }

        private void SourceSelected_CollectionChanged(object sender, NotifyCollectionChangedEventArgs e)
        {
            RefreshPossibleOps();
        }

        private void OutputSelected_CollectionChanged(object sender, NotifyCollectionChangedEventArgs e)
        {
            if (OutputSelected.Count == 1)
            {
                OutputPath.IsEnabled = true;
                OutputPath.Text = OutputSelected[0].FilePath;
            }
            else
            {
                OutputPath.IsEnabled = false;
                OutputPath.Text = string.Empty;
            }
        }

        #endregion

        private void BatchWhenAdd_PropertyChanged(DependencyObject dp, DependencyPropertyChangedEventArgs e)
        {
            RefreshButtonState();
            RefreshPossibleOps();
        }

        private IEnumerable<EntryCategory> CategoryValues
        {
            get { return (IEnumerable<EntryCategory>)GetValue(CategoryValuesProperty); }
            set { SetValue(CategoryValuesProperty, value); }
        }
        public static readonly DependencyProperty CategoryValuesProperty =
            DependencyProperty.Register("CategoryValues", typeof(IEnumerable<EntryCategory>), typeof(FileConversion), new PropertyMetadata(
                Enum.GetValues(typeof(EntryCategory)).Cast<EntryCategory>()));

        private void RefreshButtonState() // TODO: implement this with bindings
        {
            AddOp.IsEnabled = SourceSelected.Count > 0 && PossibleOps.SelectedItem != null;
            AddOutput.IsEnabled = MiddleFileView.SelectedItems.Count > 0;
            RemoveOutput.IsEnabled = ConvertedFileView.SelectedItems.Count > 0;
            RemoveItem.IsEnabled = OutputSelected.Count > 0;
            OpOptions.IsEnabled = PossibleOps.SelectedItem != null;
        }

        private void RefreshPossibleOps()
        {
            if (SourceSelected.Count > 0)
                if (BatchWhenAdd)
                {
                    PossibleOps.ItemsSource = SourceSelected
                        .Select(target => OperationFactory.EntryOperationTypes
                            .Where(op => OperationFactory.CheckOperation(op, new[] { target.Entry })))
                        .Aggregate((p, n) => p.Intersect(n))
                        .Select(type => GetOperationTuple(OperationFactory.NewOperation(type))).ToList();
                }
                else
                {
                    PossibleOps.ItemsSource = OperationFactory.EntryOperationTypes
                        .Where(op => OperationFactory.CheckOperation(op, SourceSelected.Select(target => target.Entry).ToArray()))
                        .Select(type => GetOperationTuple(OperationFactory.NewOperation(type))).ToList();
                }
            else PossibleOps.ItemsSource = Enumerable.Empty<Tuple<IArchiveEntryOperation, string>>();
        }

        private void AddOp_Click(object sender, RoutedEventArgs e)
        {
            var operation = PossibleOps.SelectedValue as IArchiveEntryOperation;
            if (BatchWhenAdd)
            {
                foreach (var item in SourceSelected)
                {
                    var output_pred = operation.Pass(new IArchiveEntry[] { item.Entry });
                    var output_list = output_pred.Select(path => new OperationTarget()
                    {
                        FilePath = path,
                        Kind = OperationTargetKind.Temporary
                    }).ToArray();
                    _owner.OperationQueue.AddOperation(new OperationDelegate()
                    {
                        Inputs = new OperationTarget[] { item },
                        Outputs = output_list,
                        Operation = operation
                    });
                    foreach(var output in output_list)
                        MiddleList.Add(output);
                }
            }
            else
            {
                var output_pred = operation.Pass(SourceSelected.Select(item => item.Entry).ToArray());
                var output_list = output_pred.Select(path => new OperationTarget()
                {
                    FilePath = path,
                    Kind = OperationTargetKind.Temporary
                }).ToArray();
                _owner.OperationQueue.AddOperation(new OperationDelegate()
                {
                    Inputs = SourceSelected.ToArray(),
                    Outputs = output_list,
                    Operation = operation
                });
                foreach (var output in output_list)
                    MiddleList.Add(output);
            }
        }

        private void OutputPath_LostKeyboardFocus(object sender, KeyboardFocusChangedEventArgs e)
        {
            OutputSelected[0].FilePath = OutputPath.Text;
        }

        private void RemoveOutput_Click(object sender, RoutedEventArgs e)
        {
            Array copy = new object[ConvertedFileView.SelectedItems.Count];
            ConvertedFileView.SelectedItems.CopyTo(copy, 0);
            foreach (OperationTarget target in copy)
            {
                OutputList.Remove(target);
                MiddleList.Add(target);
                target.Kind = OperationTargetKind.Temporary;
            }
        }

        private void AddOutput_Click(object sender, RoutedEventArgs e)
        {
            Array copy = new object[MiddleFileView.SelectedItems.Count];
            MiddleFileView.SelectedItems.CopyTo(copy, 0);
            foreach (OperationTarget target in copy)
            {
                MiddleList.Remove(target);
                OutputList.Add(target);
                target.Kind = OperationTargetKind.Output;
            }
        }

        private void RemoveItem_Click(object sender, RoutedEventArgs e)
        {
            var list = OutputSelected.SelectMany(target =>
                _owner.OperationQueue.RemoveTarget(target)).Distinct().ToArray();
            foreach (var remove in list)
            {
                MiddleList.Remove(remove);
                OutputList.Remove(remove);
            }
        }

        private void Page_KeyDown(object sender, KeyEventArgs e)
        {
            if(e.Key == Key.LeftCtrl || e.Key == Key.RightCtrl)
                _ctrl_pressed = true;
        }

        private void Page_KeyUp(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.LeftCtrl || e.Key == Key.RightCtrl)
                _ctrl_pressed = false;
        }

        private void OperationTarget_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            _focus_target = (sender as ListViewItem).DataContext as OperationTarget;
            PossibleOps.ItemsSource = new[] { GetOperationTuple(
                _owner.OperationQueue.GetPriorOperation(_focus_target).Operation) };
            PossibleOps.SelectedIndex = 0;
        }

        private void OperationTarget_MouseEnter(object sender, MouseEventArgs e)
        {
            var target = (sender as ListViewItem).DataContext as OperationTarget;
            foreach(var prior in _owner.OperationQueue.GetPriorTargets(target))
                prior.HighlightInput = true;
            foreach (var post in _owner.OperationQueue.GetPosteriorTargets(target))
                post.HighlightOutput = true;
        }

        private void OperationTarget_MouseLeave(object sender, MouseEventArgs e)
        {
            var target = (sender as ListViewItem).DataContext as OperationTarget;
            foreach (var prior in _owner.OperationQueue.GetPriorTargets(target))
                prior.HighlightInput = false;
            foreach (var post in _owner.OperationQueue.GetPosteriorTargets(target))
                post.HighlightOutput = false;
        }

        private void OpOptions_Click(object sender, RoutedEventArgs e)
        {
            if (_focus_target != null)
                throw new NotImplementedException(); // Edit exisiting operation
            else
                throw new NotImplementedException(); // Add attribute to selected operation
        }
    }
}
