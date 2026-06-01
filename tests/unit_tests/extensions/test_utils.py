# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.

"""Tests for InMemoryLoader integrity verification in extensions/utils.py."""

import hashlib
import logging
import types
from unittest.mock import patch

import pytest

from superset.extensions.utils import _compute_sha256, InMemoryLoader


def _make_module(name: str = "test_mod") -> types.ModuleType:
    return types.ModuleType(name)


def _hash_source(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# _compute_sha256
# ---------------------------------------------------------------------------


def test_compute_sha256_str():
    assert _compute_sha256("hello") == hashlib.sha256(b"hello").hexdigest()


def test_compute_sha256_bytes():
    assert _compute_sha256(b"hello") == hashlib.sha256(b"hello").hexdigest()


# ---------------------------------------------------------------------------
# exec_module – no allowlist configured (default)
# ---------------------------------------------------------------------------


@patch("superset.extensions.utils._get_allowed_hashes", return_value=None)
def test_exec_module_logs_warning_when_no_allowlist(mock_hashes, caplog):
    source = "x = 1"
    loader = InMemoryLoader("mymod", source, is_package=False, origin="test.py")
    mod = _make_module()

    with caplog.at_level(logging.WARNING, logger="superset.extensions.utils"):
        loader.exec_module(mod)

    assert mod.__dict__["x"] == 1
    assert "Executing unverified extension module" in caplog.text
    assert _hash_source(source) in caplog.text


# ---------------------------------------------------------------------------
# exec_module – allowlist configured, hash matches
# ---------------------------------------------------------------------------


@patch("superset.extensions.utils._get_allowed_hashes")
def test_exec_module_verified_hash_passes(mock_hashes, caplog):
    source = "y = 42"
    expected_hash = _hash_source(source)
    mock_hashes.return_value = {"mymod": expected_hash}

    loader = InMemoryLoader("mymod", source, is_package=False, origin="test.py")
    mod = _make_module()

    with caplog.at_level(logging.INFO, logger="superset.extensions.utils"):
        loader.exec_module(mod)

    assert mod.__dict__["y"] == 42
    assert "Executing verified extension module" in caplog.text


# ---------------------------------------------------------------------------
# exec_module – allowlist configured, module not listed
# ---------------------------------------------------------------------------


@patch("superset.extensions.utils._get_allowed_hashes")
def test_exec_module_blocked_when_not_in_allowlist(mock_hashes):
    mock_hashes.return_value = {"other_mod": "abc123"}
    source = "z = 99"
    loader = InMemoryLoader("mymod", source, is_package=False, origin="test.py")
    mod = _make_module()

    with pytest.raises(ImportError, match="not listed in EXTENSION_ALLOWED_HASHES"):
        loader.exec_module(mod)

    assert "z" not in mod.__dict__


# ---------------------------------------------------------------------------
# exec_module – allowlist configured, hash mismatch
# ---------------------------------------------------------------------------


@patch("superset.extensions.utils._get_allowed_hashes")
def test_exec_module_blocked_on_hash_mismatch(mock_hashes):
    mock_hashes.return_value = {"mymod": "wrong_hash"}
    source = "w = 7"
    loader = InMemoryLoader("mymod", source, is_package=False, origin="test.py")
    mod = _make_module()

    with pytest.raises(ImportError, match="hash mismatch"):
        loader.exec_module(mod)

    assert "w" not in mod.__dict__


# ---------------------------------------------------------------------------
# exec_module – package module sets __path__
# ---------------------------------------------------------------------------


@patch("superset.extensions.utils._get_allowed_hashes", return_value=None)
def test_exec_module_package(mock_hashes):
    source = ""
    loader = InMemoryLoader("mypkg", source, is_package=True, origin="pkg/__init__.py")
    mod = _make_module("mypkg")

    loader.exec_module(mod)

    assert mod.__path__ == []
    assert mod.__package__ == "mypkg"
