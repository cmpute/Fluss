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
using ImageMagick;

namespace JacobZ.Fluss.WinTool.Pages
{
    /// <summary>
    /// ImageEditor.xaml 的交互逻辑
    /// </summary>
    public partial class ImageEditor : Page
    {
        private string _target;
        private MagickImage _image;
        private bool _cropping = false;
        private bool _dragging = false;

        private enum HitType
        {
            None, Body, UL, UR, LR, LL, L, R, B, T
        };
        HitType _hit = HitType.None;
        Point _start;

        public ImageEditor(string target)
        {
            InitializeComponent();
            DataContext = this;
            _target = target;
            _image = new MagickImage(target);
        }

        private void Page_Loaded(object sender, RoutedEventArgs e)
        {
            SourceName.Text = System.IO.Path.GetFileName(_target);
            MainImage.Source = new BitmapImage(new Uri(_target));

            // Adjust default size
            var current_ratio = MainCanvas.ActualWidth / MainCanvas.ActualHeight;
            var fact_ratio = _image.Width / _image.Height;
            if(current_ratio < fact_ratio)
            {
                MainImage.Width = MainCanvas.ActualWidth;
                MainImage.Height = MainCanvas.ActualWidth / fact_ratio;
            }
            else
            {

                MainImage.Width = MainCanvas.ActualHeight * fact_ratio;
                MainImage.Height = MainCanvas.ActualHeight;
            }
        }

        private void CutCover_Click(object sender, RoutedEventArgs e)
        {
            const double shrink_ratio = 0.005;
            if (_cropping)
            {
                if(CropBox.Visibility == Visibility.Visible)
                {
                    // save
                }
                else return;
            }
            else
            {
                _cropping = true;
                CutCover.Content = "Save cropped";
            }

            // Set default position
            var crop_size = MainImage.ActualWidth > MainImage.ActualHeight ? MainImage.ActualHeight : MainImage.ActualWidth;
            CropBox.Width = CropBox.Height = crop_size * (1 - 2 * shrink_ratio);
            Canvas.SetLeft(CropBox, crop_size * shrink_ratio);
            Canvas.SetTop(CropBox, crop_size * shrink_ratio);
            CropBox.Visibility = Visibility.Visible;
        }

        private void MainCanvas_MouseWheel(object sender, MouseWheelEventArgs e)
        {
            const float scale_base = 2000;
            if (_cropping)
            {
                CropBox.Width *= 1 + e.Delta / scale_base;
                CropBox.Height *= 1 + e.Delta / scale_base;
            }
            else
            {
                MainImage.Width *= 1 + e.Delta / scale_base;
                MainImage.Height *= 1 + e.Delta / scale_base;
            }
        }

        private void SetHitType(Point point) => _hit = GetHitType(point);
        private HitType GetHitType(Point point)
        {
            if (!_cropping) return HitType.None; // Catch only when cropping
            double left = Canvas.GetLeft(CropBox);
            double top = Canvas.GetTop(CropBox);
            double right = left + CropBox.Width;
            double bottom = top + CropBox.Height;
            if (point.X < left) return HitType.None;
            if (point.X > right) return HitType.None;
            if (point.Y < top) return HitType.None;
            if (point.Y > bottom) return HitType.None;

            const double gap = 5;
            if (point.X - left < gap)
            {
                // Left edge.
                if (point.Y - top < gap) return HitType.UL;
                if (bottom - point.Y < gap) return HitType.LL;
                return HitType.L;
            }
            else if (right - point.X < gap)
            {
                // Right edge.
                if (point.Y - top < gap) return HitType.UR;
                if (bottom - point.Y < gap) return HitType.LR;
                return HitType.R;
            }
            if (point.Y - top < gap) return HitType.T;
            if (bottom - point.Y < gap) return HitType.B;
            return HitType.Body;
        }
        private void SetMouseCursor()
        {
            Cursor desired_cursor = Cursors.Arrow;
            switch (_hit)
            {
                case HitType.None:
                    desired_cursor = Cursors.Arrow;
                    break;
                case HitType.Body:
                    desired_cursor = Cursors.SizeAll;
                    break;
                case HitType.UL:
                case HitType.LR:
                    desired_cursor = Cursors.SizeNWSE;
                    break;
                case HitType.LL:
                case HitType.UR:
                    desired_cursor = Cursors.SizeNESW;
                    break;
                case HitType.T:
                case HitType.B:
                    desired_cursor = Cursors.SizeNS;
                    break;
                case HitType.L:
                case HitType.R:
                    desired_cursor = Cursors.SizeWE;
                    break;
            }
            if (Cursor != desired_cursor) Cursor = desired_cursor;
        }

        private void MainCanvas_MouseDown(object sender, MouseButtonEventArgs e)
        {
            SetHitType(Mouse.GetPosition(MainCanvas));
            SetMouseCursor();
            if (_hit == HitType.None) return;

            _start = Mouse.GetPosition(MainCanvas);
            _dragging = true;
        }

        private void MainCanvas_MouseUp(object sender, MouseButtonEventArgs e)
        {
            _dragging = false;
        }

        private void MainCanvas_MouseMove(object sender, MouseEventArgs e)
        {
            if (_dragging)
            {
                Point point = Mouse.GetPosition(MainCanvas);
                double offset_x = point.X - _start.X;
                double offset_y = point.Y - _start.Y;
                double offset_p = offset_y / offset_x; // Fix square ratio

                // Get the rectangle's current position.
                double new_x = Canvas.GetLeft(CropBox);
                double new_y = Canvas.GetTop(CropBox);
                double new_width = CropBox.Width;
                double new_height = CropBox.Height;

                // Update the rectangle.
                switch (_hit)
                {
                    case HitType.Body:
                        new_x += offset_x;
                        new_y += offset_y;
                        break;
                    case HitType.UL:
                        offset_x *= offset_p;
                        new_x += offset_x;
                        new_y += offset_y;
                        new_width -= offset_x;
                        new_height -= offset_y;
                        break;
                    case HitType.UR:
                        offset_x *= -offset_p;
                        new_y += offset_y;
                        new_width += offset_x;
                        new_height -= offset_y;
                        break;
                    case HitType.LR:
                        offset_x *= offset_p;
                        new_width += offset_x;
                        new_height += offset_y;
                        break;
                    case HitType.LL:
                        offset_x *= -offset_p;
                        new_x += offset_x;
                        new_width -= offset_x;
                        new_height += offset_y;
                        break;
                    case HitType.L:
                        new_x += offset_x;
                        new_width -= offset_x;
                        new_height -= offset_x;
                        break;
                    case HitType.R:
                        new_width += offset_x;
                        new_height += offset_x;
                        break;
                    case HitType.B:
                        new_width += offset_y;
                        new_height += offset_y;
                        break;
                    case HitType.T:
                        new_y += offset_y;
                        new_width -= offset_y;
                        new_height -= offset_y;
                        break;
                }

                // Don't use negative width or height.
                if ((new_width > 0) && (new_height > 0))
                {
                    // Update the rectangle.
                    Canvas.SetLeft(CropBox, new_x);
                    Canvas.SetTop(CropBox, new_y);
                    CropBox.Width = new_width;
                    CropBox.Height = new_height;

                    // Save the mouse's new location.
                    _start = point;
                }
            }
            else
            {
                SetHitType(Mouse.GetPosition(MainCanvas));
                SetMouseCursor();
            }
        }
    }
}
