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
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from superset.utils.network import _validate_host, is_host_up


@pytest.mark.parametrize(
    "host",
    [
        "example.com",
        "sub.domain.example.com",
        "192.168.1.1",
        "10.0.0.1",
        "my-host",
        "host123",
        "::1",
        "[::1]",
        "fe80::1",
    ],
)
def test_validate_host_accepts_valid_hostnames(host: str) -> None:
    _validate_host(host)


@pytest.mark.parametrize(
    "host",
    [
        "",
        "host; rm -rf /",
        "host && echo pwned",
        "host | cat /etc/passwd",
        "host`whoami`",
        "host$(id)",
        "host\nnewline",
        "-flag-injection",
        "host name with spaces",
        "host<script>",
    ],
)
def test_validate_host_rejects_invalid_hostnames(host: str) -> None:
    with pytest.raises(ValueError, match="Invalid hostname"):
        _validate_host(host)


@patch("superset.utils.network.subprocess.run")
def test_is_host_up_returns_true_on_success(mock_run: MagicMock) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=["ping", "-c", "1", "example.com"],
        returncode=0,
    )
    assert is_host_up("example.com") is True


@patch("superset.utils.network.subprocess.run")
def test_is_host_up_returns_false_on_failure(mock_run: MagicMock) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=["ping", "-c", "1", "example.com"],
        returncode=1,
    )
    assert is_host_up("example.com") is False


@patch("superset.utils.network.subprocess.run")
def test_is_host_up_returns_false_on_timeout(mock_run: MagicMock) -> None:
    mock_run.side_effect = subprocess.TimeoutExpired(cmd="ping", timeout=5)
    assert is_host_up("example.com") is False


def test_is_host_up_rejects_malicious_host() -> None:
    with pytest.raises(ValueError, match="Invalid hostname"):
        is_host_up("host; rm -rf /")


@patch("superset.utils.network.subprocess.run")
def test_is_host_up_uses_subprocess_run(mock_run: MagicMock) -> None:
    mock_run.return_value = subprocess.CompletedProcess(
        args=["ping", "-c", "1", "example.com"],
        returncode=0,
    )
    is_host_up("example.com")
    mock_run.assert_called_once()
    call_kwargs = mock_run.call_args
    assert call_kwargs.kwargs.get("capture_output") is True
    assert call_kwargs.kwargs.get("check") is False
