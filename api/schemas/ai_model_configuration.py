from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from api.services.configuration.registry import (
    AmpleVoiceAIEmbeddingsConfiguration,
    AmpleVoiceAILLMService,
    AmpleVoiceAISTTService,
    AmpleVoiceAITTSService,
    EmbeddingsConfig,
    LLMConfig,
    RealtimeConfig,
    ServiceProviders,
    STTConfig,
    TTSConfig,
)

AMPLEVOICE_SPEED_OPTIONS: tuple[float, ...] = (0.8, 1.0, 1.2)
AMPLEVOICE_DEFAULT_VOICE = "default"
AMPLEVOICE_DEFAULT_LANGUAGE = "multi"


class EffectiveAIModelConfiguration(BaseModel):
    llm: LLMConfig | None = None
    stt: STTConfig | None = None
    tts: TTSConfig | None = None
    embeddings: EmbeddingsConfig | None = None
    realtime: RealtimeConfig | None = None
    is_realtime: bool = False
    managed_service_version: int | None = None
    test_phone_number: str | None = None
    timezone: str | None = None
    last_validated_at: datetime | None = None

    @model_validator(mode="before")
    @classmethod
    def strip_incomplete_realtime_when_disabled(cls, data):
        """Skip realtime validation when is_realtime is False and api_key is missing."""
        if isinstance(data, dict) and not data.get("is_realtime", False):
            realtime = data.get("realtime")
            if isinstance(realtime, dict) and not realtime.get("api_key"):
                data.pop("realtime", None)
        return data


class AmpleVoiceAIManagedAIModelConfiguration(BaseModel):
    api_key: str
    voice: str = AMPLEVOICE_DEFAULT_VOICE
    speed: float = Field(default=1.0)
    language: str = AMPLEVOICE_DEFAULT_LANGUAGE

    @model_validator(mode="after")
    def validate_speed(self):
        if self.speed not in AMPLEVOICE_SPEED_OPTIONS:
            allowed = ", ".join(str(speed) for speed in AMPLEVOICE_SPEED_OPTIONS)
            raise ValueError(f"AmpleVoiceAI speed must be one of: {allowed}")
        return self


class BYOKPipelineAIModelConfiguration(BaseModel):
    llm: LLMConfig
    tts: TTSConfig
    stt: STTConfig
    embeddings: EmbeddingsConfig | None = None

    @model_validator(mode="after")
    def reject_amplevoice_providers(self):
        _reject_amplevoice_provider("llm", self.llm)
        _reject_amplevoice_provider("tts", self.tts)
        _reject_amplevoice_provider("stt", self.stt)
        _reject_amplevoice_provider("embeddings", self.embeddings)
        return self


class BYOKRealtimeAIModelConfiguration(BaseModel):
    realtime: RealtimeConfig
    llm: LLMConfig
    embeddings: EmbeddingsConfig | None = None

    @model_validator(mode="after")
    def reject_amplevoice_providers(self):
        _reject_amplevoice_provider("llm", self.llm)
        _reject_amplevoice_provider("embeddings", self.embeddings)
        return self


class BYOKAIModelConfiguration(BaseModel):
    mode: Literal["pipeline", "realtime"]
    pipeline: BYOKPipelineAIModelConfiguration | None = None
    realtime: BYOKRealtimeAIModelConfiguration | None = None

    @model_validator(mode="after")
    def validate_selected_mode(self):
        if self.mode == "pipeline" and self.pipeline is None:
            raise ValueError("byok.pipeline is required when byok.mode is pipeline")
        if self.mode == "realtime" and self.realtime is None:
            raise ValueError("byok.realtime is required when byok.mode is realtime")
        return self


class OrganizationAIModelConfigurationV2(BaseModel):
    version: Literal[2] = 2
    mode: Literal["amplevoice", "byok"]
    amplevoice: AmpleVoiceAIManagedAIModelConfiguration | None = None
    byok: BYOKAIModelConfiguration | None = None

    @model_validator(mode="after")
    def validate_selected_mode(self):
        if self.mode == "amplevoice" and self.amplevoice is None:
            raise ValueError("amplevoice configuration is required when mode is amplevoice")
        if self.mode == "byok" and self.byok is None:
            raise ValueError("byok configuration is required when mode is byok")
        return self


class OrganizationAIModelConfigurationResponse(BaseModel):
    configuration: dict | None
    effective_configuration: dict
    source: Literal["organization_v2", "legacy_user_v1", "empty"]


def compile_ai_model_configuration_v2(
    configuration: OrganizationAIModelConfigurationV2,
) -> EffectiveAIModelConfiguration:
    if configuration.mode == "amplevoice":
        if configuration.amplevoice is None:
            raise ValueError("amplevoice configuration is required")
        return _compile_amplevoice_configuration(configuration.amplevoice)

    if configuration.byok is None:
        raise ValueError("byok configuration is required")
    if configuration.byok.mode == "pipeline":
        if configuration.byok.pipeline is None:
            raise ValueError("byok.pipeline is required")
        pipeline = configuration.byok.pipeline
        return EffectiveAIModelConfiguration(
            llm=pipeline.llm,
            tts=pipeline.tts,
            stt=pipeline.stt,
            embeddings=pipeline.embeddings,
            is_realtime=False,
        )

    if configuration.byok.realtime is None:
        raise ValueError("byok.realtime is required")
    realtime = configuration.byok.realtime
    return EffectiveAIModelConfiguration(
        llm=realtime.llm,
        realtime=realtime.realtime,
        embeddings=realtime.embeddings,
        is_realtime=True,
    )


def _compile_amplevoice_configuration(
    configuration: AmpleVoiceAIManagedAIModelConfiguration,
) -> EffectiveAIModelConfiguration:
    return EffectiveAIModelConfiguration(
        llm=AmpleVoiceAILLMService(
            provider=ServiceProviders.AMPLEVOICE,
            api_key=configuration.api_key,
            model="default",
        ),
        tts=AmpleVoiceAITTSService(
            provider=ServiceProviders.AMPLEVOICE,
            api_key=configuration.api_key,
            model="default",
            voice=configuration.voice,
            speed=configuration.speed,
        ),
        stt=AmpleVoiceAISTTService(
            provider=ServiceProviders.AMPLEVOICE,
            api_key=configuration.api_key,
            model="default",
            language=configuration.language,
        ),
        embeddings=AmpleVoiceAIEmbeddingsConfiguration(
            provider=ServiceProviders.AMPLEVOICE,
            api_key=configuration.api_key,
            model="default",
        ),
        is_realtime=False,
        managed_service_version=2,
    )


def _reject_amplevoice_provider(section: str, service) -> None:
    if service is None:
        return
    if getattr(service, "provider", None) == ServiceProviders.AMPLEVOICE:
        raise ValueError(f"BYOK {section} cannot use AmpleVoiceAI provider")
