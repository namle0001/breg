from sqlite3 import Connection, connect, Cursor


class SQLite:
    _connection: Connection

    def __init__(self, db_path: str) -> None:
        self._connection = connect(db_path)

    def get_connection(self) -> Connection:
        return self._connection

    def close(self) -> None:
        self._connection.close()

    def cursor(self) -> Cursor:
        return self._connection.cursor()

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def execute(self, query: str, params: tuple = ()) -> Cursor:
        cursor = self._connection.cursor()
        cursor.execute(query, params)
        return cursor
