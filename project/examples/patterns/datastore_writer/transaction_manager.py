"""
Transaction management for database operations.

This module provides transaction support with automatic rollback,
savepoints, and nested transaction handling for reliable data operations.
"""

import logging
from typing import Any, Optional, Callable, Dict, List, ContextManager
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum


class IsolationLevel(Enum):
    """Database isolation levels."""
    READ_UNCOMMITTED = "READ UNCOMMITTED"
    READ_COMMITTED = "READ COMMITTED"
    REPEATABLE_READ = "REPEATABLE READ"
    SERIALIZABLE = "SERIALIZABLE"


class TransactionState(Enum):
    """Transaction states."""
    ACTIVE = "active"
    COMMITTED = "committed"
    ROLLED_BACK = "rolled_back"
    FAILED = "failed"


@dataclass
class TransactionContext:
    """Context information for transactions."""
    transaction_id: str
    isolation_level: Optional[IsolationLevel]
    start_time: float
    state: TransactionState = TransactionState.ACTIVE
    savepoints: List[str] = None
    nested_level: int = 0

    def __post_init__(self):
        """Initialize mutable fields."""
        if self.savepoints is None:
            self.savepoints = []


class TransactionError(Exception):
    """Transaction-related exception."""
    pass


class TransactionManager:
    """Manages database transactions with automatic cleanup."""

    def __init__(self, connection_pool: Any):
        """Initialize transaction manager.

        Args:
            connection_pool: Connection pool to manage transactions for
        """
        self._pool = connection_pool
        self._active_transactions: Dict[str, TransactionContext] = {}
        self._logger = logging.getLogger(__name__)

    @contextmanager
    def transaction(
        self,
        isolation_level: Optional[IsolationLevel] = None,
        readonly: bool = False
    ):
        """Context manager for database transactions.

        Args:
            isolation_level: Transaction isolation level
            readonly: Whether transaction is read-only

        Yields:
            Connection with active transaction
        """
        conn = None
        transaction_id = None

        try:
            conn = self._pool.acquire()
            transaction_id = self._begin_transaction(conn, isolation_level, readonly)

            yield conn

            self._commit_transaction(conn, transaction_id)

        except Exception as e:
            if conn and transaction_id:
                try:
                    self._rollback_transaction(conn, transaction_id)
                except Exception as rollback_error:
                    self._logger.error(f"Rollback failed: {rollback_error}")

            raise TransactionError(f"Transaction failed: {e}") from e

        finally:
            if conn:
                self._pool.release(conn)

    def _begin_transaction(
        self,
        conn: Any,
        isolation_level: Optional[IsolationLevel],
        readonly: bool
    ) -> str:
        """Begin a new transaction.

        Args:
            conn: Database connection
            isolation_level: Transaction isolation level
            readonly: Whether transaction is read-only

        Returns:
            Transaction ID
        """
        import uuid
        transaction_id = str(uuid.uuid4())

        context = TransactionContext(
            transaction_id=transaction_id,
            isolation_level=isolation_level,
            start_time=__import__('time').time()
        )

        self._active_transactions[transaction_id] = context

        try:
            # Set isolation level if specified
            if isolation_level:
                self._set_isolation_level(conn, isolation_level)

            # Set read-only if specified
            if readonly:
                self._set_readonly(conn, readonly)

            # Begin transaction
            self._execute_begin(conn)

            self._logger.debug(
                f"Started transaction {transaction_id}",
                extra={"transaction_id": transaction_id, "isolation_level": isolation_level}
            )

            return transaction_id

        except Exception as e:
            del self._active_transactions[transaction_id]
            raise TransactionError(f"Failed to begin transaction: {e}") from e

    def _commit_transaction(self, conn: Any, transaction_id: str) -> None:
        """Commit a transaction.

        Args:
            conn: Database connection
            transaction_id: Transaction to commit
        """
        if transaction_id not in self._active_transactions:
            raise TransactionError(f"Unknown transaction: {transaction_id}")

        context = self._active_transactions[transaction_id]

        try:
            self._execute_commit(conn)
            context.state = TransactionState.COMMITTED

            self._logger.debug(
                f"Committed transaction {transaction_id}",
                extra={"transaction_id": transaction_id}
            )

        except Exception as e:
            context.state = TransactionState.FAILED
            raise TransactionError(f"Failed to commit transaction: {e}") from e

        finally:
            del self._active_transactions[transaction_id]

    def _rollback_transaction(self, conn: Any, transaction_id: str) -> None:
        """Rollback a transaction.

        Args:
            conn: Database connection
            transaction_id: Transaction to rollback
        """
        if transaction_id not in self._active_transactions:
            self._logger.warning(f"Attempting to rollback unknown transaction: {transaction_id}")
            return

        context = self._active_transactions[transaction_id]

        try:
            self._execute_rollback(conn)
            context.state = TransactionState.ROLLED_BACK

            self._logger.debug(
                f"Rolled back transaction {transaction_id}",
                extra={"transaction_id": transaction_id}
            )

        except Exception as e:
            context.state = TransactionState.FAILED
            self._logger.error(f"Failed to rollback transaction {transaction_id}: {e}")

        finally:
            del self._active_transactions[transaction_id]

    def create_savepoint(self, conn: Any, transaction_id: str, name: str) -> None:
        """Create a transaction savepoint.

        Args:
            conn: Database connection
            transaction_id: Transaction ID
            name: Savepoint name
        """
        if transaction_id not in self._active_transactions:
            raise TransactionError(f"Unknown transaction: {transaction_id}")

        context = self._active_transactions[transaction_id]

        try:
            self._execute_savepoint(conn, name)
            context.savepoints.append(name)

            self._logger.debug(
                f"Created savepoint '{name}' in transaction {transaction_id}",
                extra={"transaction_id": transaction_id, "savepoint": name}
            )

        except Exception as e:
            raise TransactionError(f"Failed to create savepoint '{name}': {e}") from e

    def rollback_to_savepoint(self, conn: Any, transaction_id: str, name: str) -> None:
        """Rollback to a savepoint.

        Args:
            conn: Database connection
            transaction_id: Transaction ID
            name: Savepoint name
        """
        if transaction_id not in self._active_transactions:
            raise TransactionError(f"Unknown transaction: {transaction_id}")

        context = self._active_transactions[transaction_id]

        if name not in context.savepoints:
            raise TransactionError(f"Unknown savepoint: {name}")

        try:
            self._execute_rollback_to_savepoint(conn, name)

            # Remove savepoints created after this one
            index = context.savepoints.index(name)
            context.savepoints = context.savepoints[:index + 1]

            self._logger.debug(
                f"Rolled back to savepoint '{name}' in transaction {transaction_id}",
                extra={"transaction_id": transaction_id, "savepoint": name}
            )

        except Exception as e:
            raise TransactionError(f"Failed to rollback to savepoint '{name}': {e}") from e

    def get_transaction_stats(self) -> Dict[str, Any]:
        """Get transaction statistics."""
        return {
            "active_transactions": len(self._active_transactions),
            "transaction_details": [
                {
                    "id": ctx.transaction_id,
                    "state": ctx.state.value,
                    "start_time": ctx.start_time,
                    "nested_level": ctx.nested_level,
                    "savepoints": len(ctx.savepoints)
                }
                for ctx in self._active_transactions.values()
            ]
        }

    # Database-specific implementations (override in subclasses)

    def _set_isolation_level(self, conn: Any, level: IsolationLevel) -> None:
        """Set transaction isolation level."""
        # Default implementation - override for specific databases
        pass

    def _set_readonly(self, conn: Any, readonly: bool) -> None:
        """Set transaction read-only mode."""
        # Default implementation - override for specific databases
        pass

    def _execute_begin(self, conn: Any) -> None:
        """Execute BEGIN TRANSACTION."""
        conn.execute("BEGIN")

    def _execute_commit(self, conn: Any) -> None:
        """Execute COMMIT."""
        conn.commit()

    def _execute_rollback(self, conn: Any) -> None:
        """Execute ROLLBACK."""
        conn.rollback()

    def _execute_savepoint(self, conn: Any, name: str) -> None:
        """Execute SAVEPOINT."""
        conn.execute(f"SAVEPOINT {name}")

    def _execute_rollback_to_savepoint(self, conn: Any, name: str) -> None:
        """Execute ROLLBACK TO SAVEPOINT."""
        conn.execute(f"ROLLBACK TO SAVEPOINT {name}")


class NestedTransactionManager(TransactionManager):
    """Transaction manager supporting nested transactions."""

    def __init__(self, connection_pool: Any):
        """Initialize nested transaction manager."""
        super().__init__(connection_pool)
        self._transaction_stack: List[str] = []

    @contextmanager
    def transaction(
        self,
        isolation_level: Optional[IsolationLevel] = None,
        readonly: bool = False
    ):
        """Context manager for nested transactions.

        Args:
            isolation_level: Transaction isolation level (only for root transaction)
            readonly: Whether transaction is read-only (only for root transaction)

        Yields:
            Connection with active transaction
        """
        if self._transaction_stack:
            # Nested transaction - create savepoint
            parent_transaction_id = self._transaction_stack[-1]
            conn = None

            try:
                # Get connection from parent transaction
                # This is a simplified implementation
                conn = self._pool.acquire()
                savepoint_name = f"nested_{len(self._transaction_stack)}"

                # Create savepoint instead of new transaction
                self.create_savepoint(conn, parent_transaction_id, savepoint_name)

                yield conn

            except Exception as e:
                if conn and parent_transaction_id:
                    try:
                        self.rollback_to_savepoint(conn, parent_transaction_id, savepoint_name)
                    except Exception:
                        pass
                raise TransactionError(f"Nested transaction failed: {e}") from e

            finally:
                if conn:
                    self._pool.release(conn)

        else:
            # Root transaction
            with super().transaction(isolation_level, readonly) as conn:
                self._transaction_stack.append(self._active_transactions.keys()[-1] if self._active_transactions else "unknown")
                try:
                    yield conn
                finally:
                    if self._transaction_stack:
                        self._transaction_stack.pop()

