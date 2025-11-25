using System;
using System.Collections.Generic;
using System.Text;

namespace PathcraftAI.Core
{
    /// <summary>
    /// POE DAT64 파일 파서
    /// DAT64는 64비트 오프셋을 사용하는 POE의 바이너리 데이터 포맷
    /// </summary>
    public class Dat64Parser
    {
        private byte[] _data = Array.Empty<byte>();
        private int _rowCount;
        private int _dataStart;
        private int _variableDataStart;

        /// <summary>
        /// 파싱된 행 수
        /// </summary>
        public int RowCount => _rowCount;

        /// <summary>
        /// 변수 데이터 섹션 시작 위치
        /// </summary>
        public int VariableDataStart => _variableDataStart;

        /// <summary>
        /// DAT64 파일 로드
        /// </summary>
        public bool Load(byte[] data)
        {
            if (data == null || data.Length < 4)
            {
                Console.Error.WriteLine("[ERROR] Invalid DAT64 data");
                return false;
            }

            _data = data;
            _dataStart = 4;

            // 첫 4바이트: 행 수
            _rowCount = BitConverter.ToInt32(data, 0);

            // 변수 데이터 섹션 마커 찾기 (0xBBBBBBBBBBBBBBBB)
            _variableDataStart = FindVariableDataMarker();

            return true;
        }

        /// <summary>
        /// 변수 데이터 섹션 마커 찾기
        /// </summary>
        private int FindVariableDataMarker()
        {
            // 마커: 8바이트의 0xBB
            for (int i = _dataStart; i < _data.Length - 7; i++)
            {
                bool isMarker = true;
                for (int j = 0; j < 8; j++)
                {
                    if (_data[i + j] != 0xBB)
                    {
                        isMarker = false;
                        break;
                    }
                }
                if (isMarker)
                {
                    return i + 8; // 마커 다음부터 시작
                }
            }
            return _data.Length;
        }

        /// <summary>
        /// 고정 데이터 섹션에서 특정 위치의 값 읽기
        /// </summary>
        public int ReadInt32(int offset)
        {
            return BitConverter.ToInt32(_data, offset);
        }

        public uint ReadUInt32(int offset)
        {
            return BitConverter.ToUInt32(_data, offset);
        }

        public long ReadInt64(int offset)
        {
            return BitConverter.ToInt64(_data, offset);
        }

        public ulong ReadUInt64(int offset)
        {
            return BitConverter.ToUInt64(_data, offset);
        }

        public short ReadInt16(int offset)
        {
            return BitConverter.ToInt16(_data, offset);
        }

        public ushort ReadUInt16(int offset)
        {
            return BitConverter.ToUInt16(_data, offset);
        }

        public byte ReadByte(int offset)
        {
            return _data[offset];
        }

        public bool ReadBool(int offset)
        {
            return _data[offset] != 0;
        }

        public float ReadFloat(int offset)
        {
            return BitConverter.ToSingle(_data, offset);
        }

        /// <summary>
        /// 변수 데이터 섹션에서 UTF-16LE 문자열 읽기
        /// </summary>
        public string? ReadString(long relativeOffset)
        {
            if (relativeOffset == 0)
                return null;

            int absoluteOffset = _variableDataStart + (int)relativeOffset;
            if (absoluteOffset < 0 || absoluteOffset >= _data.Length)
                return null;

            // 널 종료자 찾기 (2바이트 0x00 0x00)
            int length = 0;
            while (absoluteOffset + length + 1 < _data.Length)
            {
                if (_data[absoluteOffset + length] == 0 && _data[absoluteOffset + length + 1] == 0)
                    break;
                length += 2;
            }

            if (length == 0)
                return string.Empty;

            return Encoding.Unicode.GetString(_data, absoluteOffset, length);
        }

        /// <summary>
        /// 리스트 데이터 읽기 (크기 + 오프셋)
        /// </summary>
        public (long count, long offset) ReadListHeader(int offset)
        {
            long count = ReadInt64(offset);
            long listOffset = ReadInt64(offset + 8);
            return (count, listOffset);
        }

        /// <summary>
        /// 문자열 리스트 읽기
        /// </summary>
        public List<string> ReadStringList(int offset)
        {
            var result = new List<string>();
            var (count, listOffset) = ReadListHeader(offset);

            if (count == 0)
                return result;

            int absoluteOffset = _variableDataStart + (int)listOffset;
            for (int i = 0; i < count; i++)
            {
                // 각 요소는 8바이트 문자열 오프셋
                long stringOffset = BitConverter.ToInt64(_data, absoluteOffset + i * 8);
                var str = ReadString(stringOffset);
                if (str != null)
                    result.Add(str);
            }

            return result;
        }

        /// <summary>
        /// 특정 행의 시작 오프셋 계산
        /// </summary>
        public int GetRowOffset(int rowIndex, int rowSize)
        {
            return _dataStart + (rowIndex * rowSize);
        }

        /// <summary>
        /// 원본 데이터 접근
        /// </summary>
        public byte[] GetRawData() => _data;

        /// <summary>
        /// 고정 데이터 섹션 크기
        /// </summary>
        public int FixedDataSize => _variableDataStart - _dataStart - 8; // 마커 8바이트 제외
    }

    /// <summary>
    /// DAT64 필드 타입
    /// </summary>
    public enum Dat64FieldType
    {
        Bool,
        Int8,
        UInt8,
        Int16,
        UInt16,
        Int32,
        UInt32,
        Int64,
        UInt64,
        Float,
        String,         // 8바이트 오프셋
        List,           // 16바이트 (count + offset)
        ForeignKey      // 8바이트 오프셋
    }

    /// <summary>
    /// DAT64 필드 정의
    /// </summary>
    public class Dat64Field
    {
        public string Name { get; set; } = string.Empty;
        public Dat64FieldType Type { get; set; }
        public Dat64FieldType? ListElementType { get; set; }

        /// <summary>
        /// 필드의 바이트 크기
        /// </summary>
        public int Size => Type switch
        {
            Dat64FieldType.Bool => 1,
            Dat64FieldType.Int8 => 1,
            Dat64FieldType.UInt8 => 1,
            Dat64FieldType.Int16 => 2,
            Dat64FieldType.UInt16 => 2,
            Dat64FieldType.Int32 => 4,
            Dat64FieldType.UInt32 => 4,
            Dat64FieldType.Int64 => 8,
            Dat64FieldType.UInt64 => 8,
            Dat64FieldType.Float => 4,
            Dat64FieldType.String => 8,
            Dat64FieldType.List => 16,
            Dat64FieldType.ForeignKey => 8,
            _ => 0
        };
    }

    /// <summary>
    /// DAT64 테이블 스키마
    /// </summary>
    public class Dat64Schema
    {
        public string TableName { get; set; } = string.Empty;
        public List<Dat64Field> Fields { get; set; } = new();

        /// <summary>
        /// 행 크기 계산
        /// </summary>
        public int CalculateRowSize()
        {
            int size = 0;
            foreach (var field in Fields)
            {
                size += field.Size;
            }
            return size;
        }
    }
}
