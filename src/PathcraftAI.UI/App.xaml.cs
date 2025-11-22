using System.Configuration;
using System.Data;
using System.Diagnostics;
using System.IO;
using System.Windows;

namespace PathcraftAI.UI;

/// <summary>
/// Interaction logic for App.xaml
/// </summary>
public partial class App : Application
{
    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        // 전역 예외 핸들러 등록
        DispatcherUnhandledException += App_DispatcherUnhandledException;
        AppDomain.CurrentDomain.UnhandledException += CurrentDomain_UnhandledException;
    }

    private void App_DispatcherUnhandledException(object sender, System.Windows.Threading.DispatcherUnhandledExceptionEventArgs e)
    {
        LogException("DispatcherUnhandledException", e.Exception);

        MessageBox.Show(
            $"예기치 않은 오류가 발생했습니다.\n\n{e.Exception.Message}\n\n자세한 내용은 crash_log.txt를 확인하세요.",
            "오류",
            MessageBoxButton.OK,
            MessageBoxImage.Error);

        e.Handled = true; // 앱 종료 방지
    }

    private void CurrentDomain_UnhandledException(object sender, UnhandledExceptionEventArgs e)
    {
        if (e.ExceptionObject is Exception ex)
        {
            LogException("UnhandledException", ex);
        }
    }

    private void LogException(string source, Exception ex)
    {
        try
        {
            var logPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "crash_log.txt");
            var logMessage = $"[{DateTime.Now:yyyy-MM-dd HH:mm:ss}] {source}\n" +
                           $"Message: {ex.Message}\n" +
                           $"StackTrace:\n{ex.StackTrace}\n" +
                           $"InnerException: {ex.InnerException?.Message}\n" +
                           new string('=', 80) + "\n\n";

            File.AppendAllText(logPath, logMessage);
            Debug.WriteLine(logMessage);
        }
        catch
        {
            // 로깅 실패 무시
        }
    }
}
