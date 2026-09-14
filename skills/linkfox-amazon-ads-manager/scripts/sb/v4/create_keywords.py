#!/usr/bin/env python3
"""Create SB keywords for V4 campaign management.

Required JSON: profileId, region, payload (Amazon-native request body).
Uses Amazon shared sb/keywords targeting path; this is not a V4->V3 fallback.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _sb_common import run_mutation  # noqa: E402

if __name__ == "__main__":
    run_mutation(
        __doc__,
        path="sb/keywords",
        method="POST",
        content_type="application/json",
        accept="application/vnd.sbkeywordresponse.v3+json",
        api_version="V4",
        resource_version="V3_SHARED_TARGETING",
    )
