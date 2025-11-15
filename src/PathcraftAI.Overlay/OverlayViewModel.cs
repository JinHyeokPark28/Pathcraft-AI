using System.ComponentModel;
using System.Runtime.CompilerServices;

namespace PathcraftAI.Overlay
{
    public sealed class OverlayViewModel : INotifyPropertyChanged
    {
        private string _name = "캐릭터: (대기)";
        private string _class = "";
        private string _dps = "DPS: -";
        private string _ehp = "EHP: -";
        private string _res = "Res: -";

        public string CharacterName { get => _name; set { _name = value; OnChanged(); } }
        public string ClassAsc { get => _class; set { _class = value; OnChanged(); } }
        public string DpsText { get => _dps; set { _dps = value; OnChanged(); } }
        public string EhpText { get => _ehp; set { _ehp = value; OnChanged(); } }
        public string ResText { get => _res; set { _res = value; OnChanged(); } }

        public event PropertyChangedEventHandler? PropertyChanged;
        private void OnChanged([CallerMemberName] string? n = null)
            => PropertyChanged?.Invoke(this, new PropertyChangedEventArgs(n));
    }
}
