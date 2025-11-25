using System;
using System.Collections.Generic;
using System.IO;
using Microsoft.Data.Sqlite;

namespace PathcraftAI.UI
{
    public class BuildBookmark
    {
        public int Id { get; set; }
        public string BuildName { get; set; } = "";
        public string PobUrl { get; set; } = "";
        public string PobCode { get; set; } = "";
        public string ClassName { get; set; } = "";
        public string MainSkill { get; set; } = "";
        public int Level { get; set; }
        public string? Notes { get; set; }
        public string? Tags { get; set; }
        public DateTime CreatedAt { get; set; }
        public DateTime? UpdatedAt { get; set; }
    }

    public class BookmarkService : IDisposable
    {
        private readonly string _connectionString;

        public BookmarkService()
        {
            var dbPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "bookmarks.db");
            _connectionString = $"Data Source={dbPath}";
            InitializeDatabase();
        }

        private void InitializeDatabase()
        {
            using var connection = new SqliteConnection(_connectionString);
            connection.Open();

            var command = connection.CreateCommand();
            command.CommandText = @"
                CREATE TABLE IF NOT EXISTS bookmarks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    build_name TEXT NOT NULL,
                    pob_url TEXT,
                    pob_code TEXT,
                    class_name TEXT,
                    main_skill TEXT,
                    level INTEGER DEFAULT 0,
                    notes TEXT,
                    tags TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_bookmarks_class ON bookmarks(class_name);
                CREATE INDEX IF NOT EXISTS idx_bookmarks_skill ON bookmarks(main_skill);
            ";
            command.ExecuteNonQuery();
        }

        public int AddBookmark(BuildBookmark bookmark)
        {
            using var connection = new SqliteConnection(_connectionString);
            connection.Open();

            var command = connection.CreateCommand();
            command.CommandText = @"
                INSERT INTO bookmarks (build_name, pob_url, pob_code, class_name, main_skill, level, notes, tags, created_at)
                VALUES (@build_name, @pob_url, @pob_code, @class_name, @main_skill, @level, @notes, @tags, @created_at);
                SELECT last_insert_rowid();
            ";

            command.Parameters.AddWithValue("@build_name", bookmark.BuildName);
            command.Parameters.AddWithValue("@pob_url", bookmark.PobUrl ?? "");
            command.Parameters.AddWithValue("@pob_code", bookmark.PobCode ?? "");
            command.Parameters.AddWithValue("@class_name", bookmark.ClassName ?? "");
            command.Parameters.AddWithValue("@main_skill", bookmark.MainSkill ?? "");
            command.Parameters.AddWithValue("@level", bookmark.Level);
            command.Parameters.AddWithValue("@notes", bookmark.Notes ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@tags", bookmark.Tags ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@created_at", DateTime.Now.ToString("o"));

            return Convert.ToInt32(command.ExecuteScalar());
        }

        public List<BuildBookmark> GetAllBookmarks()
        {
            var bookmarks = new List<BuildBookmark>();

            using var connection = new SqliteConnection(_connectionString);
            connection.Open();

            var command = connection.CreateCommand();
            command.CommandText = "SELECT * FROM bookmarks ORDER BY created_at DESC";

            using var reader = command.ExecuteReader();
            while (reader.Read())
            {
                bookmarks.Add(ReadBookmark(reader));
            }

            return bookmarks;
        }

        public BuildBookmark? GetBookmark(int id)
        {
            using var connection = new SqliteConnection(_connectionString);
            connection.Open();

            var command = connection.CreateCommand();
            command.CommandText = "SELECT * FROM bookmarks WHERE id = @id";
            command.Parameters.AddWithValue("@id", id);

            using var reader = command.ExecuteReader();
            if (reader.Read())
            {
                return ReadBookmark(reader);
            }

            return null;
        }

        public void UpdateBookmark(BuildBookmark bookmark)
        {
            using var connection = new SqliteConnection(_connectionString);
            connection.Open();

            var command = connection.CreateCommand();
            command.CommandText = @"
                UPDATE bookmarks
                SET build_name = @build_name,
                    pob_url = @pob_url,
                    pob_code = @pob_code,
                    class_name = @class_name,
                    main_skill = @main_skill,
                    level = @level,
                    notes = @notes,
                    tags = @tags,
                    updated_at = @updated_at
                WHERE id = @id
            ";

            command.Parameters.AddWithValue("@id", bookmark.Id);
            command.Parameters.AddWithValue("@build_name", bookmark.BuildName);
            command.Parameters.AddWithValue("@pob_url", bookmark.PobUrl ?? "");
            command.Parameters.AddWithValue("@pob_code", bookmark.PobCode ?? "");
            command.Parameters.AddWithValue("@class_name", bookmark.ClassName ?? "");
            command.Parameters.AddWithValue("@main_skill", bookmark.MainSkill ?? "");
            command.Parameters.AddWithValue("@level", bookmark.Level);
            command.Parameters.AddWithValue("@notes", bookmark.Notes ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@tags", bookmark.Tags ?? (object)DBNull.Value);
            command.Parameters.AddWithValue("@updated_at", DateTime.Now.ToString("o"));

            command.ExecuteNonQuery();
        }

        public void DeleteBookmark(int id)
        {
            using var connection = new SqliteConnection(_connectionString);
            connection.Open();

            var command = connection.CreateCommand();
            command.CommandText = "DELETE FROM bookmarks WHERE id = @id";
            command.Parameters.AddWithValue("@id", id);
            command.ExecuteNonQuery();
        }

        public List<BuildBookmark> SearchBookmarks(string? searchTerm = null, string? className = null, string? mainSkill = null)
        {
            var bookmarks = new List<BuildBookmark>();

            using var connection = new SqliteConnection(_connectionString);
            connection.Open();

            var command = connection.CreateCommand();
            var conditions = new List<string>();

            if (!string.IsNullOrWhiteSpace(searchTerm))
            {
                conditions.Add("(build_name LIKE @search OR notes LIKE @search OR tags LIKE @search)");
                command.Parameters.AddWithValue("@search", $"%{searchTerm}%");
            }

            if (!string.IsNullOrWhiteSpace(className))
            {
                conditions.Add("class_name = @class_name");
                command.Parameters.AddWithValue("@class_name", className);
            }

            if (!string.IsNullOrWhiteSpace(mainSkill))
            {
                conditions.Add("main_skill LIKE @main_skill");
                command.Parameters.AddWithValue("@main_skill", $"%{mainSkill}%");
            }

            var whereClause = conditions.Count > 0 ? $"WHERE {string.Join(" AND ", conditions)}" : "";
            command.CommandText = $"SELECT * FROM bookmarks {whereClause} ORDER BY created_at DESC";

            using var reader = command.ExecuteReader();
            while (reader.Read())
            {
                bookmarks.Add(ReadBookmark(reader));
            }

            return bookmarks;
        }

        public int GetBookmarkCount()
        {
            using var connection = new SqliteConnection(_connectionString);
            connection.Open();

            var command = connection.CreateCommand();
            command.CommandText = "SELECT COUNT(*) FROM bookmarks";
            return Convert.ToInt32(command.ExecuteScalar());
        }

        private BuildBookmark ReadBookmark(SqliteDataReader reader)
        {
            return new BuildBookmark
            {
                Id = reader.GetInt32(reader.GetOrdinal("id")),
                BuildName = reader.GetString(reader.GetOrdinal("build_name")),
                PobUrl = reader.IsDBNull(reader.GetOrdinal("pob_url")) ? "" : reader.GetString(reader.GetOrdinal("pob_url")),
                PobCode = reader.IsDBNull(reader.GetOrdinal("pob_code")) ? "" : reader.GetString(reader.GetOrdinal("pob_code")),
                ClassName = reader.IsDBNull(reader.GetOrdinal("class_name")) ? "" : reader.GetString(reader.GetOrdinal("class_name")),
                MainSkill = reader.IsDBNull(reader.GetOrdinal("main_skill")) ? "" : reader.GetString(reader.GetOrdinal("main_skill")),
                Level = reader.IsDBNull(reader.GetOrdinal("level")) ? 0 : reader.GetInt32(reader.GetOrdinal("level")),
                Notes = reader.IsDBNull(reader.GetOrdinal("notes")) ? null : reader.GetString(reader.GetOrdinal("notes")),
                Tags = reader.IsDBNull(reader.GetOrdinal("tags")) ? null : reader.GetString(reader.GetOrdinal("tags")),
                CreatedAt = DateTime.Parse(reader.GetString(reader.GetOrdinal("created_at"))),
                UpdatedAt = reader.IsDBNull(reader.GetOrdinal("updated_at")) ? null : DateTime.Parse(reader.GetString(reader.GetOrdinal("updated_at")))
            };
        }

        public void Dispose()
        {
            // Connection is created and disposed per-method
            // No persistent connection to dispose
        }
    }
}
