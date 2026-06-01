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


@patch("superset.utils.rls.get_predicates_for_table")
@patch("superset.utils.rls.SQLScript")
def test_collect_rls_predicates_for_sql_returns_sorted_predicates(
    mock_sql_script: MagicMock,
    mock_get_predicates: MagicMock,
) -> None:
    from superset.utils.rls import collect_rls_predicates_for_sql

    table = MagicMock()
    table.qualify.return_value = table
    statement = MagicMock()
    statement.tables = [table]
    mock_sql_script.return_value.statements = [statement]
    mock_get_predicates.return_value = ["b_pred", "a_pred"]

    database = MagicMock()
    database.db_engine_spec.engine = "postgresql"
    database.get_default_catalog.return_value = None

    result = collect_rls_predicates_for_sql("SELECT * FROM t", database, None, "public")
    assert result == ["a_pred", "b_pred"]


@patch("superset.utils.rls.SQLScript")
def test_collect_rls_predicates_for_sql_parse_error_returns_sentinel(
    mock_sql_script: MagicMock,
    caplog: pytest.LogCaptureFixture,
) -> None:
    from superset.utils.rls import collect_rls_predicates_for_sql

    mock_sql_script.side_effect = ValueError("bad sql")

    database = MagicMock()
    database.db_engine_spec.engine = "postgresql"

    with caplog.at_level(logging.ERROR, logger="superset.utils.rls"):
        result = collect_rls_predicates_for_sql("INVALID SQL", database, None, "public")

    assert len(result) == 1
    assert result[0].startswith("__rls_parse_error_")
    assert "Failed to collect RLS predicates for SQL" in caplog.text


@patch("superset.utils.rls.SQLScript")
def test_collect_rls_predicates_sentinel_is_unique_per_call(
    mock_sql_script: MagicMock,
) -> None:
    from superset.utils.rls import collect_rls_predicates_for_sql

    mock_sql_script.side_effect = ValueError("bad sql")

    database = MagicMock()
    database.db_engine_spec.engine = "postgresql"

    result1 = collect_rls_predicates_for_sql("INVALID SQL", database, None, "public")
    result2 = collect_rls_predicates_for_sql("INVALID SQL", database, None, "public")

    assert result1 != result2
