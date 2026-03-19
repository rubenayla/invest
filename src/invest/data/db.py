"""
Central database connection factory.

All database access goes through this module. Connection string is read from
the DB_URL environment variable, falling back to ~/.invest_db_url, then to
localhost:5432 (direct connection on server).

Mac (via SSH tunnel):  DB_URL=postgresql://invest:invest_2026@localhost:5433/invest
Server (direct):       DB_URL=postgresql://invest:invest_2026@localhost:5432/invest
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

import psycopg2
import psycopg2.extras


def _resolve_db_url() -> str:
    """Resolve database URL from environment, config file, or default."""
    url = os.environ.get('DB_URL')
    if url:
        return url

    config_file = Path.home() / '.invest_db_url'
    if config_file.exists():
        return config_file.read_text().strip()

    return 'postgresql://invest:invest_2026@localhost:5432/invest'


@lru_cache(maxsize=1)
def get_db_url() -> str:
    """Get the database URL (cached)."""
    return _resolve_db_url()


def get_connection(dict_cursor: bool = False):
    """
    Get a new psycopg2 connection.

    Parameters
    ----------
    dict_cursor : bool
        If True, use RealDictCursor so rows behave like dicts.

    Returns
    -------
    psycopg2.extensions.connection
    """
    kwargs = {}
    if dict_cursor:
        kwargs['cursor_factory'] = psycopg2.extras.RealDictCursor
    return psycopg2.connect(get_db_url(), **kwargs)


def get_engine():
    """Get a SQLAlchemy engine for pandas read_sql / to_sql."""
    from sqlalchemy import create_engine
    return create_engine(get_db_url())
