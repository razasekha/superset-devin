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
"""Test hash algorithm migration for shared entries."""

from unittest.mock import MagicMock, patch
from uuid import uuid3


def test_get_shared_value_no_fallback() -> None:
    """Test that get_shared_value returns None when no fallback is configured."""
    from superset.key_value.shared_entries import get_shared_value
    from superset.key_value.types import SharedKey

    key = SharedKey.DASHBOARD_PERMALINK_SALT

    mock_dao = MagicMock()
    mock_dao.get_value.return_value = None

    mock_app = MagicMock()
    mock_app.config = {
        "HASH_ALGORITHM": "sha256",
        "HASH_ALGORITHM_FALLBACKS": [],
    }

    with patch("superset.key_value.shared_entries.KeyValueDAO", mock_dao):
        with patch("superset.key_value.utils.current_app", mock_app):
            result = get_shared_value(key)

    assert result is None
    # Only one lookup (primary SHA-256), no fallback
    assert mock_dao.get_value.call_count == 1


def test_get_shared_value_finds_sha256_first() -> None:
    """Test that get_shared_value finds SHA-256 entry without fallback."""
    from superset.key_value.shared_entries import get_shared_value
    from superset.key_value.types import SharedKey
    from superset.key_value.utils import get_uuid_namespace_with_algorithm

    key = SharedKey.DASHBOARD_PERMALINK_SALT
    expected_value = "new_sha256_salt"

    namespace_sha256 = get_uuid_namespace_with_algorithm("", "sha256")
    uuid_sha256 = uuid3(namespace_sha256, key)

    mock_dao = MagicMock()

    def mock_get_value(resource, uuid_key, codec):
        if uuid_key == uuid_sha256:
            return expected_value
        return None

    mock_dao.get_value.side_effect = mock_get_value

    mock_app = MagicMock()
    mock_app.config = {
        "HASH_ALGORITHM": "sha256",
        "HASH_ALGORITHM_FALLBACKS": [],
    }

    with patch("superset.key_value.shared_entries.KeyValueDAO", mock_dao):
        with patch("superset.key_value.utils.current_app", mock_app):
            result = get_shared_value(key)

    assert result == expected_value
    assert mock_dao.get_value.call_count == 1
