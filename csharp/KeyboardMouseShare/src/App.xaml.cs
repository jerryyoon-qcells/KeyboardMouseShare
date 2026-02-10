using System;
using System.IO;
using System.Windows;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.Logging;
using Serilog;
using Serilog.Core;
using KeyboardMouseShare.Services;

namespace KeyboardMouseShare
{
    /// <summary>
    /// Interaction logic for App.xaml
    /// </summary>
    public partial class App : Application
    {
        private ILogger<App>? _logger;
        private ILoggerFactory? _loggerFactory;

        private void Application_Startup(object sender, StartupEventArgs e)
        {
            try
            {
                // Load configuration
                var config = LoadConfiguration();
                
                // Setup logging
                _loggerFactory = SetupLogging(config);
                _logger = _loggerFactory.CreateLogger<App>();
                
                _logger.LogInformation("Starting Keyboard Mouse Share application");
                _logger.LogInformation("Version: 1.0.0");
                _logger.LogInformation("Platform: {OS}", Environment.OSVersion);

                // Parse command-line arguments
                ParseArguments(e.Args);
            }
            catch (Exception ex)
            {
                _logger?.LogCritical(ex, "Failed to start application");
                MessageBox.Show(
                    $"Failed to start application: {ex.Message}",
                    "Application Error",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error);
                Shutdown(1);
            }
        }

        private void Application_Exit(object sender, ExitEventArgs e)
        {
            _logger?.LogInformation("Application shutting down");
            (_loggerFactory as IDisposable)?.Dispose();
        }

        /// <summary>
        /// Load configuration from config file
        /// </summary>
        private static IConfiguration LoadConfiguration()
        {
            var configPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "KeyboardMouseShare",
                "config.json"
            );

            var configBuilder = new ConfigurationBuilder()
                .SetBasePath(AppDomain.CurrentDomain.BaseDirectory)
                .AddJsonFile("appsettings.json", optional: true, reloadOnChange: true);

            if (File.Exists(configPath))
            {
                configBuilder.AddJsonFile(configPath, optional: true, reloadOnChange: true);
            }

            return configBuilder.Build();
        }

        /// <summary>
        /// Setup logging using Serilog
        /// </summary>
        private static ILoggerFactory SetupLogging(IConfiguration config)
        {
            var logPath = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
                "KeyboardMouseShare",
                "logs"
            );

            Directory.CreateDirectory(logPath);

            Log.Logger = new LoggerConfiguration()
                .MinimumLevel.Debug()
                .WriteTo.Console()
                .WriteTo.File(
                    Path.Combine(logPath, "kms.log"),
                    rollingInterval: RollingInterval.Day,
                    retainedFileCountLimit: 7)
                .CreateLogger();

            var loggerFactory = LoggerFactory.Create(builder =>
            {
                builder.AddSerilog();
            });

            return loggerFactory;
        }

        /// <summary>
        /// Parse command-line arguments
        /// </summary>
        private static void ParseArguments(string[] args)
        {
            foreach (var arg in args)
            {
                if (arg == "--debug")
                {
                    // Enable debug mode
                }
            }
        }
    }
}
