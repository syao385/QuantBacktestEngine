import sqlite3
import json
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Optional

class StrategyRepository:
    """
    SQLite Strategy Spec & Version Lineage Repository for QuantBacktestEngine.
    Stores strategy specs, version progression (v1.0 -> v1.1), parameter diffs,
    and historical backtest execution run archives.
    """

    def __init__(self, db_path: str = "strategies.db"):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        """Creates strategy_registry and backtest_runs tables if they do not exist."""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategy_registry (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    description TEXT,
                    spec_json TEXT NOT NULL,
                    spec_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, version)
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    strategy_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    parameters_json TEXT,
                    metrics_json TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def save_strategy(
        self,
        name: str,
        version: str,
        spec: Dict[str, Any],
        description: str = ""
    ) -> int:
        spec_json = json.dumps(spec, sort_keys=True)
        spec_hash = hashlib.sha256(spec_json.encode('utf-8')).hexdigest()

        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO strategy_registry (name, version, description, spec_json, spec_hash)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(name, version) DO UPDATE SET
                    description = excluded.description,
                    spec_json = excluded.spec_json,
                    spec_hash = excluded.spec_hash
            """, (name, version, description, spec_json, spec_hash))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def get_strategy(self, name: str, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            if version:
                cursor.execute("SELECT id, name, version, description, spec_json, created_at FROM strategy_registry WHERE name = ? AND version = ?", (name, version))
            else:
                cursor.execute("SELECT id, name, version, description, spec_json, created_at FROM strategy_registry WHERE name = ? ORDER BY id DESC LIMIT 1", (name,))
            
            row = cursor.fetchone()
            if not row:
                return None
            
            return {
                "id": row[0],
                "name": row[1],
                "version": row[2],
                "description": row[3],
                "spec": json.loads(row[4]),
                "created_at": row[5]
            }
        finally:
            conn.close()

    def list_strategies(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name, version, description, created_at FROM strategy_registry ORDER BY name, id DESC")
            rows = cursor.fetchall()
            return [
                {
                    "id": r[0],
                    "name": r[1],
                    "version": r[2],
                    "description": r[3],
                    "created_at": r[4]
                }
                for r in rows
            ]
        finally:
            conn.close()

    def save_run(
        self,
        strategy_name: str,
        version: str,
        symbol: str,
        parameters: Dict[str, Any],
        metrics: Dict[str, Any]
    ) -> int:
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO backtest_runs (strategy_name, version, symbol, parameters_json, metrics_json)
                VALUES (?, ?, ?, ?, ?)
            """, (strategy_name, version, symbol, json.dumps(parameters), json.dumps(metrics)))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()
