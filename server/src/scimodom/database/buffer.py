from typing import Generic, TypeVar, List

from sqlalchemy.orm import Session

T = TypeVar("T")  # Should be SqlAlchemy model class


class InsertBuffer(Generic[T]):
    """Utility class to insert data to selected model tables. It implements
    the contact manager interface, which may be used to ensure flushing in case
    the object goes out-of-scope without error.

    :param session: SQLAlchemy ORM session
    :type session: Session
    :param auto_flush: Imported data is flushed and committed by
    default. If set to false this parameter prevents flush and commit,
    allowing to access the records before they are eventually inserted
    into the database.
    :type auto_flush: bool
    :param buffer_size: Maximal number of record before flushing.
    :type buffer_size: int
    """

    def __init__(
        self, session: Session, auto_flush: bool = True, buffer_size: int = 1000
    ) -> None:
        """Initializer method."""
        self._session = session
        self._auto_flush = auto_flush
        self._buffer_size = buffer_size

        self.buffer: List[T] = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is None:
            self.flush()

    def queue(self, item: T) -> None:
        """Buffers data and flush if required."""
        self.buffer.append(item)
        if self._auto_flush and len(self.buffer) >= self._buffer_size:
            self.flush()

    def flush(self) -> None:
        """Insert and reset buffer."""
        if len(self.buffer) == 0:
            return
        self._session.add_all(self.buffer)
        self._session.commit()
        self.buffer = []
