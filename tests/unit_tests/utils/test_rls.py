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
import logging
from unittest.mock import MagicMock, patch

import pytest

from superset.utils.rls import collect_rls_predicates_for_sql


def test_collect_rls_predicates_for_sql_raises_on_parse_failure() -> None:
    """When SQL parsing fails, the exception should propagate (not be swallowed)
    so the caller forces a cache miss instead of producing a cache key that
    silently ignores RLS predicates."""
    database = MagicMock()
    database.db_engine_spec.engine = "postgresql"

    with patch(
        "superset.utils.rls.SQLScript",
        side_effect=ValueError("unparsable SQL"),
    ):
        with pytest.raises(ValueError, match="unparsable SQL"):
            collect_rls_predicates_for_sql(
                sql="NOT VALID SQL",
                database=database,
                catalog=None,
                schema="public",
            )


def test_collect_rls_predicates_for_sql_logs_warning_on_parse_failure(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When SQL parsing fails, a warning should be logged with the exception
    details so operators can detect the problem."""
    database = MagicMock()
    database.db_engine_spec.engine = "postgresql"

    with patch(
        "superset.utils.rls.SQLScript",
        side_effect=ValueError("unparsable SQL"),
    ):
        with caplog.at_level(logging.WARNING, logger="superset.utils.rls"):
            with pytest.raises(ValueError):
                collect_rls_predicates_for_sql(
                    sql="NOT VALID SQL",
                    database=database,
                    catalog=None,
                    schema="public",
                )

    assert any(
        "Failed to parse SQL for RLS cache key computation" in record.message
        for record in caplog.records
    )


def test_collect_rls_predicates_for_sql_success() -> None:
    """Happy path: valid SQL should return sorted RLS predicates without raising."""
    database = MagicMock()
    database.db_engine_spec.engine = "postgresql"
    database.get_default_catalog.return_value = None

    mock_table = MagicMock()
    mock_table.qualify.return_value = mock_table

    mock_statement = MagicMock()
    mock_statement.tables = [mock_table]

    mock_script = MagicMock()
    mock_script.statements = [mock_statement]

    with (
        patch("superset.utils.rls.SQLScript", return_value=mock_script),
        patch(
            "superset.utils.rls.get_predicates_for_table",
            return_value=["role = 'admin'", "dept_id = 1"],
        ),
    ):
        result = collect_rls_predicates_for_sql(
            sql="SELECT * FROM t",
            database=database,
            catalog=None,
            schema="public",
        )

    assert result == ["dept_id = 1", "role = 'admin'"]
