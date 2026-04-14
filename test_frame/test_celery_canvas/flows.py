from __future__ import annotations

import traceback
from typing import Any, Dict, List, Tuple

from celery import chain, chord, group, signature

from .celery_app import app
from .tasks import (
    add,
    aggregate_dicts,
    concat_strings,
    download_video,
    error_prone,
    fetch_url,
    mul,
    on_error_collect,
    raise_ignore,
    send_finish_msg,
    retryable_task,
    sleep_task,
    sum_list,
    to_pair,
)


def flow_chain_basics(x: int = 3, y: int = 5) -> Any:
    # Chain: (x + y) * 8
    c = chain(add.s(x, y), mul.s(8))
    return c.apply_async().get()


def flow_group_and_chord(urls: List[str]) -> Dict[str, Any]:
    # group parallel fetch -> chord aggregate
    g = group(fetch_url.s(url) for url in urls)
    result = chord(g)(aggregate_dicts.s()).get()
    return result


def flow_chord_with_error_callback(values: List[int]) -> Dict[str, Any]:
    # Trigger custom error callback on failure
    g = group(error_prone.s(v) for v in values)
    try:
        res = chord(g)(sum_list.s()).get()
        return {"ok": True, "sum": res}
    except Exception as exc:  # Catch chord exception, trigger custom collection
        tb = traceback.format_exc()
        collected = on_error_collect.apply_async(kwargs={"request": {}, "exc": str(exc), "traceback_str": tb}).get()
        return {"ok": False, "error": collected}


def flow_nested_chain_group(values: List[int]) -> List[Any]:
    # Nested: chain containing group, then further tasks
    g = group(retryable_task.s(v) for v in values)
    c = chain(g, sum_list.s())
    return c.apply_async().get()


def flow_map_and_starmap(numbers: List[int]) -> Tuple[List[int], List[int]]:
    # map: map list as single-argument
    mapped = group(add.s(n, 1) for n in numbers).apply_async().get()
    # starmap: expand multiple arguments
    pairs = group(to_pair.s(n) for n in numbers).apply_async().get()
    starmapped = group(mul.s(a, b) for a, b in pairs).apply_async().get()
    return mapped, starmapped


def flow_chain_link_error_ignored() -> Dict[str, Any]:
    # A step returns Ignore; subsequent steps are not affected (chain is interrupted; use link_error or try/except as fallback)
    try:
        c = chain(raise_ignore.s("skip"), add.s(1))
        res = c.apply_async().get()
        return {"reached": True, "res": res}
    except Exception as exc:
        return {"reached": False, "exc": str(exc)}


def flow_complex_mix(urls: List[str], numbers: List[int]) -> Dict[str, Any]:
    # Complex combination:
    # - chord(fetch_url) -> aggregate
    # - chain(sum_list(numbers), mul(2))
    # - group(retryable_task(numbers))
    # Finally aggregate with concat_strings
    chord_part = chord(group(fetch_url.s(u) for u in urls))(aggregate_dicts.s())
    chain_part = chain(group(add.s(n, 0) for n in numbers), sum_list.s(), mul.s(2))
    retry_part = group(retryable_task.s(v) for v in numbers)

    g = group(
        signature("celery.accumulate").s([1, 2, 3]),  # Celery 内置示例（若不可用忽略结果）
        chord_part,
        chain_part,
        retry_part,
        sleep_task.s(0.2),
    )
    results = g.apply_async().get(propagate=False)

    # Handle the case where built-in tasks don't exist or fail
    pretty = []
    for item in results:
        try:
            if isinstance(item, Exception):
                pretty.append(f"EXC:{item}")
            else:
                pretty.append(str(item))
        except Exception as exc:
            pretty.append(f"EXC:{exc}")

    summary = concat_strings.apply_async(args=[pretty]).get()
    return {"items": pretty, "summary": summary}


def flow_video_pipeline(url: str) -> Dict[str, Any]:
    """Convert funboost example to Celery canvas:

    Equivalent flow:
    chain(download_video(url), chord(group(transform_video(file, r) for r in [360p,720p,1080p]), send_finish_msg(files, url)))

    Expressed as: first download to get file -> header(group) generates multiple resolutions -> body converges and sends finish message.
    """
    # 1) First download the video
    # 2) header: transcode downloaded file in parallel
    header = group(
        download_video.s(url) | signature("test_frame.test_celery_canvas.tasks.transform_video").s(res)
        for res in ["360p", "720p", "1080p"]
    )
    # 3) body: aggregate and send finish message (body's parameter receives header's list result)
    body = send_finish_msg.s(url=url)
    ch = chord(header, body)
    return ch.apply_async().get()


FLOWS = {
    "chain_basics": flow_chain_basics,
    "group_chord": flow_group_and_chord,
    "chord_with_error_callback": flow_chord_with_error_callback,
    "nested_chain_group": flow_nested_chain_group,
    "map_and_starmap": flow_map_and_starmap,
    "chain_link_error_ignored": flow_chain_link_error_ignored,
    "complex_mix": flow_complex_mix,
    "video_pipeline": flow_video_pipeline,
}


def run_flow_by_name(name: str, *args, **kwargs):
    fn = FLOWS.get(name)
    if not fn:
        raise KeyError(f"unknown flow: {name}")
    return fn(*args, **kwargs)


