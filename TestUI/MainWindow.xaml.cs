﻿using System;
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
using JacobC.Music.Crawlers.Astost;

namespace TestUI
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

        AstostCrawler ac = new AstostCrawler(null);

        private async void Window_Loaded(object sender, RoutedEventArgs e)
        {
            ac.LogService += (message) => System.Diagnostics.Debug.WriteLine(message);
            VerifyImage.Source = BitmapFrame.Create(await ac.GetVerifyCode());
        }

        private async void Button_Click(object sender, RoutedEventArgs e)
        {
            Status.Text = "Logging in";
            Status.Text = (await ac.Login(Username.Text, Password.Password, Code.Text)).ToString();
        }

        private void Button_Click_1(object sender, RoutedEventArgs e)
        {
            Status.Text = "Logging out";
            ac.Logout();
        }
    }
}