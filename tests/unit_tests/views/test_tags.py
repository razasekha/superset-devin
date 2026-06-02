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
"""Tests for superset.views.tags module pagination"""

from unittest.mock import MagicMock, patch

from superset.tags.models import Tag
from superset.views.tags import DEFAULT_PAGE_SIZE


def _make_tag(id_: int) -> MagicMock:
    tag = MagicMock(spec=Tag)
    tag.id = id_
    tag.type.name = "custom"
    tag.name = f"tag-{id_}"
    tag.changed_on = None
    tag.changed_by_fk = None
    tag.created_by_fk = None
    return tag


@patch("superset.views.tags.is_feature_enabled", return_value=True)
@patch("superset.views.tags.db")
def test_tags_returns_paginated_response(
    mock_db: MagicMock,
    mock_feature: MagicMock,
    app_context: None,
) -> None:
    """The tags endpoint should return a paginated response with count and result."""
    from flask import Flask

    from superset.views.tags import TagView

    app = Flask(__name__)
    tags = [_make_tag(i) for i in range(3)]

    mock_query = MagicMock()
    mock_db.session.query.return_value = mock_query
    mock_query.count.return_value = 3
    mock_query.offset.return_value.limit.return_value.all.return_value = tags

    view = TagView()
    with app.test_request_context("/tags/?page=0&page_size=10"):
        with patch.object(view, "ensure_enabled", return_value=None):
            response = view.tags()

    data = response.get_json()
    assert data["count"] == 3
    assert len(data["result"]) == 3
    mock_query.offset.assert_called_once_with(0)
    mock_query.offset.return_value.limit.assert_called_once_with(10)


@patch("superset.views.tags.is_feature_enabled", return_value=True)
@patch("superset.views.tags.db")
def test_tags_defaults_page_size(
    mock_db: MagicMock,
    mock_feature: MagicMock,
    app_context: None,
) -> None:
    """Without page_size the endpoint should default to DEFAULT_PAGE_SIZE."""
    from flask import Flask

    from superset.views.tags import TagView

    app = Flask(__name__)
    mock_query = MagicMock()
    mock_db.session.query.return_value = mock_query
    mock_query.count.return_value = 0
    mock_query.offset.return_value.limit.return_value.all.return_value = []

    view = TagView()
    with app.test_request_context("/tags/"):
        with patch.object(view, "ensure_enabled", return_value=None):
            view.tags()

    mock_query.offset.assert_called_once_with(0)
    mock_query.offset.return_value.limit.assert_called_once_with(DEFAULT_PAGE_SIZE)


@patch("superset.views.tags.is_feature_enabled", return_value=True)
@patch("superset.views.tags.db")
def test_tags_caps_page_size(
    mock_db: MagicMock,
    mock_feature: MagicMock,
    app_context: None,
) -> None:
    """page_size larger than DEFAULT_PAGE_SIZE should be capped."""
    from flask import Flask

    from superset.views.tags import TagView

    app = Flask(__name__)
    mock_query = MagicMock()
    mock_db.session.query.return_value = mock_query
    mock_query.count.return_value = 0
    mock_query.offset.return_value.limit.return_value.all.return_value = []

    view = TagView()
    with app.test_request_context("/tags/?page_size=9999"):
        with patch.object(view, "ensure_enabled", return_value=None):
            view.tags()

    mock_query.offset.return_value.limit.assert_called_once_with(DEFAULT_PAGE_SIZE)


@patch("superset.views.tags.is_feature_enabled", return_value=True)
@patch("superset.views.tags.db")
def test_tags_page_offset(
    mock_db: MagicMock,
    mock_feature: MagicMock,
    app_context: None,
) -> None:
    """page=2 with page_size=10 should offset by 20."""
    from flask import Flask

    from superset.views.tags import TagView

    app = Flask(__name__)
    mock_query = MagicMock()
    mock_db.session.query.return_value = mock_query
    mock_query.count.return_value = 50
    mock_query.offset.return_value.limit.return_value.all.return_value = []

    view = TagView()
    with app.test_request_context("/tags/?page=2&page_size=10"):
        with patch.object(view, "ensure_enabled", return_value=None):
            view.tags()

    mock_query.offset.assert_called_once_with(20)
    mock_query.offset.return_value.limit.assert_called_once_with(10)
