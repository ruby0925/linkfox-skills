#!/usr/bin/env python3
"""List SB V4 ad creatives.

Required JSON: profileId, region, adId. Pass Amazon-native list body in payload;
filters/maxResults/nextToken are also accepted at the top level.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from _sb_common import emit_structured_error, parse_argv_params, run_post_token_list  # noqa: E402

if __name__ == "__main__":
    params = parse_argv_params(__doc__)
    body = dict(params.get("payload") or {})
    if params.get("adId") and "adId" not in body:
        body["adId"] = str(params["adId"])
    if not body.get("adId"):
        emit_structured_error(
            code="SB_CREATIVE_AD_ID_REQUIRED",
            message="adId is required for sb/ads/creatives/list.",
            extra={"apiVersion": "V4", "path": "sb/ads/creatives/list"},
        )
    run_post_token_list(
        __doc__,
        path="sb/ads/creatives/list",
        content_type="application/vnd.sbAdCreativeResource.v4+json",
        accept="application/vnd.sbAdCreativeResource.v4+json",
        response_key="creatives",
        api_version="V4",
        resource_version="V4",
        params=params,
        request_body=body,
    )
