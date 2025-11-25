using System;
using System.Windows;
using System.Windows.Input;

namespace PathcraftAI.UI
{
    public partial class BookmarksWindow : Window
    {
        private readonly BookmarkService _bookmarkService;
        public BuildBookmark? SelectedBookmark { get; private set; }

        public BookmarksWindow()
        {
            InitializeComponent();
            _bookmarkService = new BookmarkService();
            LoadBookmarks();
        }

        private void LoadBookmarks(string? searchTerm = null)
        {
            var bookmarks = string.IsNullOrWhiteSpace(searchTerm)
                ? _bookmarkService.GetAllBookmarks()
                : _bookmarkService.SearchBookmarks(searchTerm);

            BookmarksList.ItemsSource = bookmarks;
            BookmarkCountText.Text = $"{bookmarks.Count} bookmarks";
        }

        private void Search_Click(object sender, RoutedEventArgs e)
        {
            LoadBookmarks(SearchBox.Text);
        }

        private void SearchBox_KeyDown(object sender, KeyEventArgs e)
        {
            if (e.Key == Key.Enter)
            {
                LoadBookmarks(SearchBox.Text);
            }
        }

        private void Delete_Click(object sender, RoutedEventArgs e)
        {
            if (BookmarksList.SelectedItem is BuildBookmark bookmark)
            {
                var result = MessageBox.Show(
                    $"Delete bookmark '{bookmark.BuildName}'?",
                    "Confirm Delete",
                    MessageBoxButton.YesNo,
                    MessageBoxImage.Question);

                if (result == MessageBoxResult.Yes)
                {
                    _bookmarkService.DeleteBookmark(bookmark.Id);
                    LoadBookmarks(SearchBox.Text);
                }
            }
            else
            {
                MessageBox.Show("Please select a bookmark to delete.",
                    "No Selection", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void LoadPOB_Click(object sender, RoutedEventArgs e)
        {
            if (BookmarksList.SelectedItem is BuildBookmark bookmark)
            {
                SelectedBookmark = bookmark;
                DialogResult = true;
                Close();
            }
            else
            {
                MessageBox.Show("Please select a bookmark to load.",
                    "No Selection", MessageBoxButton.OK, MessageBoxImage.Information);
            }
        }

        private void BookmarksList_MouseDoubleClick(object sender, MouseButtonEventArgs e)
        {
            if (BookmarksList.SelectedItem is BuildBookmark bookmark)
            {
                SelectedBookmark = bookmark;
                DialogResult = true;
                Close();
            }
        }

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            DialogResult = false;
            Close();
        }
    }
}
