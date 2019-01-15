using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.CompilerServices;
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
        public IArchiveEntry Entry
        {
            get { return _entry; }
            set
            {
                if (_entry == value)
                    return;
                _entry = value; OnPropertyChanged();
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
