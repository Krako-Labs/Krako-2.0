from __future__ import annotations

import hashlib

BASE_BACKOFF_SECONDS = 0.5
MAX_BACKOFF_SECONDS = 30.0

RETRYABLE_ERRORS = {
    "network_transient",
    "node_timeout",
    "admission_reject",
}

CRITICAL_PRIORITIES = {"critical", "p0", "p1"}

_HASH64_TEST_VECTORS = {
    "": "e3b0c44298fc1c14",
    "a": "ca978112ca1bbdca",
    "krako": "6f25630f4b8f1977",
}


def hash64(value: str) -> int:
    digest = hashlib.sha256(value.encode("utf-8")).digest()
    return int.from_bytes(digest[:8], byteorder="big", signed=False)


def is_retryable_error(error_code: str) -> bool:
    return error_code in RETRYABLE_ERRORS


def compute_backoff_seconds(work_unit_id: str, attempt_index: int) -> float:
    k = max(1, int(attempt_index))
    d_exp = BASE_BACKOFF_SECONDS * (2 ** (k - 1))
    ratio = hash64(f"{work_unit_id}:{k}") / (2**64)
    jitter = ratio * 0.2 * d_exp
    return min(MAX_BACKOFF_SECONDS, d_exp + jitter)


def max_attempts(congestion_mode: str, priority: str) -> int:
    mode = (congestion_mode or "NORMAL").upper()
    prio = (priority or "").lower()
    if mode == "HIGH" and prio not in CRITICAL_PRIORITIES:
        return 3
    return 5


def verify_hash64_test_vectors() -> bool:
    for raw, expected_prefix in _HASH64_TEST_VECTORS.items():
        digest_prefix = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]
        if digest_prefix != expected_prefix:
            return False
    return True
