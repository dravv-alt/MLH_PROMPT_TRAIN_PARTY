"""Fail-closed generation-provider selection.

Hosted generation is never selected merely because a callable exists. Both the
provider selection and explicit opt-in are required, and the default is local.
"""
from dataclasses import dataclass
import os


@dataclass(frozen=True)
class GenerationConfig:
    provider: str = "local"
    hosted_opt_in: bool = False

    @classmethod
    def from_environment(cls) -> "GenerationConfig":
        provider = os.getenv("SANCTUARY_GENERATION_PROVIDER", "local").strip().casefold()
        if provider not in {"local", "hosted"}:
            provider = "local"
        opt_in = os.getenv("SANCTUARY_HOSTED_GENERATION_OPT_IN", "false").strip().casefold() in {"1", "true", "yes"}
        return cls(provider=provider, hosted_opt_in=opt_in)
