"""AmpleVoiceAI subclass of pipecat's Gemini Live Vertex AI LLM service.

Diamond inheritance: combines the AmpleVoiceAI engine-integration overrides from
:class:`AmpleVoiceAIGeminiLiveLLMService` with the Vertex-specific tweaks from
upstream's :class:`GeminiLiveVertexLLMService` (no history config,
``NON_BLOCKING`` tools disabled, service-account credentials).

MRO::

    AmpleVoiceAIGeminiLiveVertexLLMService
      -> AmpleVoiceAIGeminiLiveLLMService
      -> GeminiLiveVertexLLMService
      -> GeminiLiveLLMService
      -> LLMService
      -> ...
"""

from api.services.pipecat.realtime.gemini_live import AmpleVoiceAIGeminiLiveLLMService
from pipecat.services.google.gemini_live.vertex.llm import (
    GeminiLiveVertexLLMService,
)


class AmpleVoiceAIGeminiLiveVertexLLMService(
    AmpleVoiceAIGeminiLiveLLMService,
    GeminiLiveVertexLLMService,
):
    """Vertex AI variant of Gemini Live with AmpleVoiceAI integration quirks."""

    pass


# Guard against MRO regressions: a future refactor that flips inheritance
# order or breaks the diamond would silently bypass the AmpleVoiceAI overrides.
_mro = AmpleVoiceAIGeminiLiveVertexLLMService.__mro__
assert _mro[1] is AmpleVoiceAIGeminiLiveLLMService, (
    f"Expected AmpleVoiceAIGeminiLiveLLMService at MRO[1], got {_mro[1]}"
)
assert _mro[2] is GeminiLiveVertexLLMService, (
    f"Expected GeminiLiveVertexLLMService at MRO[2], got {_mro[2]}"
)
del _mro
