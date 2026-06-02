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
from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest

from superset.key_value.exceptions import KeyValueParseKeyError
from superset.key_value.types import KeyValueResource

RESOURCE = KeyValueResource.APP
UUID_KEY = UUID("3e7a2ab8-bcaf-49b0-a5df-dfb432f291cc")
ID_KEY = 123


@pytest.mark.parametrize(
    "key,expected_filter",
    [
        (UUID_KEY, {"resource": RESOURCE, "uuid": UUID_KEY}),
        (ID_KEY, {"resource": RESOURCE, "id": ID_KEY}),
    ],
    ids=["uuid_key", "id_key"],
)
def test_get_filter(key, expected_filter) -> None:
    """Test get_filter with different key types."""
    from superset.key_value.utils import get_filter

    assert get_filter(resource=RESOURCE, key=key) == expected_filter


def test_encode_permalink_id_valid() -> None:
    """Test encoding permalink ID with valid input."""
    from superset.key_value.utils import encode_permalink_key

    salt = "abc"
    assert encode_permalink_key(1, salt) == "AyBn4lm9qG8"


def test_decode_permalink_id_invalid() -> None:
    """Test decoding permalink ID with invalid input."""
    from superset.key_value.utils import decode_permalink_id

    with pytest.raises(KeyValueParseKeyError):
        decode_permalink_id("foo", "bar")


def test_get_uuid_namespace() -> None:
    """Test UUID namespace generation with SHA-256."""
    from superset.key_value.utils import get_uuid_namespace

    mock_app = MagicMock()
    mock_app.config = {"HASH_ALGORITHM": "sha256"}
    namespace = get_uuid_namespace("test_seed", app=mock_app)

    assert isinstance(namespace, UUID)
    assert namespace == UUID("4504d44d-861b-6919-7db1-d95e47344234")


def test_get_uuid_namespace_deterministic() -> None:
    """Test that UUID namespace generation is deterministic."""
    from superset.key_value.utils import get_uuid_namespace

    mock_app = MagicMock()
    mock_app.config = {"HASH_ALGORITHM": "sha256"}
    namespace1 = get_uuid_namespace("same_seed", app=mock_app)
    namespace2 = get_uuid_namespace("same_seed", app=mock_app)
    assert namespace1 == namespace2


def test_get_uuid_namespace_different_seeds() -> None:
    """Test that different seeds produce different UUID namespaces."""
    from superset.key_value.utils import get_uuid_namespace

    mock_app = MagicMock()
    mock_app.config = {"HASH_ALGORITHM": "sha256"}
    namespace1 = get_uuid_namespace("seed1", app=mock_app)
    namespace2 = get_uuid_namespace("seed2", app=mock_app)
    assert namespace1 != namespace2


def test_get_uuid_namespace_with_algorithm() -> None:
    """Test UUID namespace generation with explicit SHA-256 algorithm."""
    from superset.key_value.utils import get_uuid_namespace_with_algorithm

    namespace = get_uuid_namespace_with_algorithm("test_seed", "sha256")
    assert isinstance(namespace, UUID)
    assert namespace == UUID("4504d44d-861b-6919-7db1-d95e47344234")


def test_get_uuid_namespace_with_algorithm_md5_raises() -> None:
    """Test that MD5 raises ValueError after deprecation."""
    from superset.key_value.utils import get_uuid_namespace_with_algorithm

    with pytest.raises(ValueError, match="Unsupported hash algorithm"):
        get_uuid_namespace_with_algorithm("test_seed", "md5")


def test_get_deterministic_uuid_with_algorithm() -> None:
    """Test deterministic UUID generation with SHA-256."""
    from superset.key_value.utils import get_deterministic_uuid_with_algorithm

    payload = {"key": "value", "number": 123}

    uuid_1 = get_deterministic_uuid_with_algorithm("salt", payload, "sha256")
    uuid_2 = get_deterministic_uuid_with_algorithm("salt", payload, "sha256")
    assert uuid_1 == uuid_2


def test_get_deterministic_uuid_md5_raises() -> None:
    """Test that MD5 raises ValueError for deterministic UUID generation."""
    from superset.key_value.utils import get_deterministic_uuid_with_algorithm

    payload = {"key": "value", "number": 123}

    with pytest.raises(ValueError, match="Unsupported hash algorithm"):
        get_deterministic_uuid_with_algorithm("salt", payload, "md5")


def test_get_fallback_algorithms_empty_default() -> None:
    """Test that fallback algorithms default to empty list."""
    from superset.key_value.utils import get_fallback_algorithms

    mock_app = MagicMock()
    mock_app.config = {"HASH_ALGORITHM_FALLBACKS": []}
    fallbacks = get_fallback_algorithms(app=mock_app)

    assert fallbacks == []


def test_get_fallback_algorithms_default() -> None:
    """Test fallback algorithms default to empty list if not configured."""
    from superset.key_value.utils import get_fallback_algorithms

    mock_app = MagicMock()
    mock_app.config = {}  # No HASH_ALGORITHM_FALLBACKS key
    fallbacks = get_fallback_algorithms(app=mock_app)

    assert fallbacks == []
