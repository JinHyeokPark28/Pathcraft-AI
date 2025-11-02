using PathcraftAI.Core.Models;
using PathcraftAI.Core.Services;

namespace PathcraftAI.LLM
{
    public interface IReasoningProvider
    {
        int Fill(BuildModel model);
    }

    // 템플릿 기반 로컬 구현 (추후 ChatGPT/Gemini 등으로 대체 가능)
    public sealed class LocalTemplateReasoningProvider : IReasoningProvider
    {
        private readonly ReasoningFiller _filler;
        public LocalTemplateReasoningProvider(string reasoningDir)
        {
            _filler = ReasoningFiller.LoadFrom(reasoningDir);
        }
        public int Fill(BuildModel model) => _filler.FillMissing(model);
    }
}
