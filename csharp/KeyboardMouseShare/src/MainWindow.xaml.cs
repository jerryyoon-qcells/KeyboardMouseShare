using System.Windows;

namespace KeyboardMouseShare.UI
{
    /// <summary>
    /// WPF Main Window for Keyboard Mouse Share application
    /// </summary>
    public partial class MainWindow : Window
    {

        public MainWindow()
        {
            InitializeComponent();
            Title = "Keyboard Mouse Share - v1.0.0";
        }

        /// <summary>
        /// Window loaded event handler
        /// </summary>
        private void Window_Loaded(object sender, RoutedEventArgs e)
        {
            // Initialize UI components
            // Load configuration
            // Initialize services
        }

        /// <summary>
        /// Handle window closing
        /// </summary>
        private void Window_Closing(object sender, System.ComponentModel.CancelEventArgs e)
        {
            // Cleanup resources
            // Save configuration
        }
    }
}
