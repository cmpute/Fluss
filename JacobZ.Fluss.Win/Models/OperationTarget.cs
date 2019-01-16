using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.CompilerServices;
using JacobZ.Fluss.Utils;
using SharpCompress.Archives;

namespace JacobZ.Fluss.Win.Models
{
    public sealed class OperationTarget : INotifyPropertyChanged
    {
        public OperationTarget()
        {
            System.Diagnostics.Debug.WriteLine(GetHashCode());
        }

        public OperationTargetKind Kind { get; set; }

        IArchiveEntry _entry;
        // Return source entry for source target, or dummy entry for generated target
        public IArchiveEntry Entry
        {
            get
            {
                return Kind == OperationTargetKind.Input ? _entry : new DirectoryArchiveEntry(FilePath);
            }
            set
            {
                if (_entry == value)
                    return;
                _entry = value;
                FilePath = Entry.Key;
                OnPropertyChanged();
            }
        }

        string _filepath = string.Empty;
        // Return source key for source target, or custom name for generated target
        public string FilePath
        {
            get { return Kind == OperationTargetKind.Input ? _entry.Key : _filepath; }
            set
            {
                if (_filepath == value)
                    return;
                _filepath = value;
                OnPropertyChanged();
            }
        }

        bool _is_input_hl = false, _is_output_hl = false;
        public bool HighlightInput
        {
            get { return _is_input_hl; }
            set
            {
                if (_is_input_hl == value)
                    return;
                _is_input_hl = value;
                OnPropertyChanged();
            }
        }
        public bool HighlightOutput
        {
            get { return _is_output_hl; }
            set
            {
                if (_is_output_hl == value)
                    return;
                _is_output_hl = value;
                OnPropertyChanged();
            }
        }

        public event PropertyChangedEventHandler PropertyChanged;
        void OnPropertyChanged([CallerMemberName] string propertyName = null)
        {
            PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(propertyName));
        }
    }

    public enum OperationTargetKind
    {
        Input,
        Output,
        Temporary
    }
}
