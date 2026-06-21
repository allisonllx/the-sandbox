"""Route challenges to legacy hardcoded scaffolds vs dynamic factory."""

from __future__ import annotations

import os

from ..ai_pm.models import ChallengeTrack

_FACTORY_MODE = os.getenv("CHALLENGE_FACTORY_MODE", "auto")


def challenge_factory_mode() -> str:
    return _FACTORY_MODE


def use_legacy_factory(item_id: str, track: ChallengeTrack | None = None) -> bool:
    """
    Legacy path: hardcoded starter_scaffold / synthesizer / global secret tests.

    auto: demo-* and product track use legacy until Phase 3 product factory ships.
    """
    mode = _FACTORY_MODE
    if mode == "legacy":
        return True
    if mode == "dynamic":
        return track == ChallengeTrack.product_feature
    # auto
    if item_id.startswith("demo-"):
        return True
    if track == ChallengeTrack.product_feature:
        return True
    return False
