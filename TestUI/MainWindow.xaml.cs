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
using JacobC.Music.Crawlers.Astost;
using JacobC.Music.Crawlers;

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
            ac = new AstostCrawler(cw) { SaveCookie = true };
            ac.LogService += (message) => System.Diagnostics.Debug.WriteLine(message);
            AdditionTask();
        }

        async void AdditionTask()
        {
            Status.Text = (await ac.CheckLogin()) ? "Already Logged in" : "Not Logged in";
        }

        CsvWriter<AstostArticleInfo> cw = new CsvWriter<AstostArticleInfo>(@"C:\Users\cmpute\Desktop\test.csv");
        AstostCrawler ac;

        private async void Window_Loaded(object sender, RoutedEventArgs e)
        {
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

        private async void Button_Click_2(object sender, RoutedEventArgs e)
        {
            ac.StartPostID = 11007500;
            ac.GrabForumList = new uint[] { 42 };
            await ac.StartCrawling();
            MessageBox.Show("爬虫完成");
        }

        private async void VerifyImage_MouseDown(object sender, MouseButtonEventArgs e)
        {
            VerifyImage.Source = BitmapFrame.Create(await ac.GetVerifyCode());
        }
    }
}
