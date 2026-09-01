"""Database access layer for the Concordance System.

This file is responsible for the connection to Oracle
and for running SQL queries and commands.
Other parts of the project use this file instead of
connecting to Oracle directly.
"""

import contextlib

import oracledb

import config


# Shared Oracle connection.
_connection = None

# Number of active transaction blocks.
_transaction_depth = 0


def get_connection():
    """Returns the shared Oracle connection."""

    global _connection

    # Open the connection only when it is first needed.
    if _connection is None:
        _connection = oracledb.connect(**config.connect_kwargs())

    return _connection


def close():
    """Closes the shared Oracle connection."""

    global _connection

    if _connection is not None:
        _connection.close()
        _connection = None


def commit():
    """Commits the current changes to the database."""

    # A transaction block decides when the final commit happens.
    if _transaction_depth:
        return

    get_connection().commit()


def rollback():
    """Rolls back the current database changes."""

    # A transaction block decides when the final rollback happens.
    if _transaction_depth:
        return

    get_connection().rollback()


@contextlib.contextmanager
def transaction():
    """Runs several operations as one transaction.

    If all operations succeed, the transaction is committed.
    If one operation fails, all changes are rolled back.
    """

    global _transaction_depth

    # Enter a transaction block.
    _transaction_depth += 1

    try:
        yield

    except Exception:
        # Leave the current transaction level.
        _transaction_depth -= 1

        # Only the outer transaction performs the rollback.
        if _transaction_depth == 0:
            get_connection().rollback()

        raise

    else:
        # Leave the current transaction level.
        _transaction_depth -= 1

        # Only the outer transaction performs the commit.
        if _transaction_depth == 0:
            get_connection().commit()


def _rows_to_dicts(cursor):
    """Converts query results to dictionaries."""

    # Use the column names as dictionary keys.
    columns = [description[0].lower() for description in cursor.description]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]


def run_query(sql, params=None):
    """Runs a SELECT query and returns the rows as dictionaries."""

    cursor = get_connection().cursor()

    try:
        cursor.execute(sql, params or {})
        return _rows_to_dicts(cursor)

    finally:
        # Always close the cursor.
        cursor.close()


def run_command(sql, params=None):
    """Runs an INSERT, UPDATE or DELETE command.

    Returns the number of affected rows.
    The caller decides when to commit.
    """

    cursor = get_connection().cursor()

    try:
        cursor.execute(sql, params or {})
        return cursor.rowcount

    finally:
        cursor.close()


def executemany(sql, rows):
    """Runs the same SQL command for many rows.

    Used for bulk inserts.
    Returns the number of affected rows.
    """

    # Nothing to insert.
    if not rows:
        return 0

    cursor = get_connection().cursor()

    try:
        cursor.executemany(sql, rows)
        return cursor.rowcount

    finally:
        cursor.close()


def insert_returning_id(sql, params, returning_bind="new_id"):
    """Runs an INSERT and returns the new generated ID."""

    cursor = get_connection().cursor()

    try:
        # Variable that receives the ID created by Oracle.
        out_var = cursor.var(oracledb.NUMBER)

        # Copy the parameters and add the output variable.
        bind = dict(params)
        bind[returning_bind] = out_var

        cursor.execute(sql, bind)
        value = out_var.getvalue()

        # Oracle may return the value inside a list.
        if isinstance(value, list):
            value = value[0]

        return int(value)

    finally:
        cursor.close()