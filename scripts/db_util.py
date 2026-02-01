#!/usr/bin/env python3
"""
Database dump/load utility for TrendCloset SQLite database.

Usage:
    # Dump to SQL file
    python scripts/db_util.py dump --format sql --output backup.sql
    
    # Dump to JSON file
    python scripts/db_util.py dump --format json --output backup.json
    
    # Load from SQL file
    python scripts/db_util.py load --format sql --input backup.sql
    
    # Load from JSON file
    python scripts/db_util.py load --format json --input backup.json
    
    # List tables and row counts
    python scripts/db_util.py info
"""

import argparse
import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from app.config import get_settings


def get_db_path() -> Path:
    """Get the database file path from settings."""
    settings = get_settings()
    # Parse sqlite:///./data/story_threads.db
    db_url = settings.database_url
    if db_url.startswith("sqlite:///"):
        # Handle both absolute and relative paths
        path_str = db_url[10:]  # Remove sqlite:///
        if path_str.startswith("./"):
            # Relative to backend directory
            backend_dir = Path(__file__).parent.parent / "backend"
            return backend_dir / path_str[2:]
        else:
            return Path(path_str)
    raise ValueError(f"Unsupported database URL: {db_url}")


def dump_sql(db_path: Path, output_path: Path) -> None:
    """Dump database to SQL file."""
    conn = sqlite3.connect(db_path)
    
    with open(output_path, 'w') as f:
        f.write(f"-- TrendCloset Database Dump\n")
        f.write(f"-- Generated: {datetime.now().isoformat()}\n")
        f.write(f"-- Source: {db_path}\n\n")
        f.write("BEGIN TRANSACTION;\n\n")
        
        # Dump schema and data
        for line in conn.iterdump():
            f.write(line + "\n")
        
        f.write("\nCOMMIT;\n")
    
    conn.close()
    print(f"✅ Dumped database to {output_path}")


def load_sql(db_path: Path, input_path: Path) -> None:
    """Load database from SQL file."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    with open(input_path, 'r') as f:
        sql_script = f.read()
    
    # Execute the SQL script
    cursor.executescript(sql_script)
    conn.commit()
    conn.close()
    
    print(f"✅ Loaded database from {input_path}")


def serialize_value(value: Any) -> Any:
    """Serialize a value for JSON output."""
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def dump_json(db_path: Path, output_path: Path) -> None:
    """Dump database to JSON file."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    data = {
        "metadata": {
            "dumped_at": datetime.now().isoformat(),
            "source": str(db_path),
            "tables": tables
        },
        "tables": {}
    }
    
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        
        table_data = []
        for row in rows:
            row_dict = dict(zip(row.keys(), row))
            table_data.append(row_dict)
        
        data["tables"][table] = table_data
    
    conn.close()
    
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=2, default=str)
    
    print(f"✅ Dumped database to {output_path}")
    print(f"   Tables: {', '.join(tables)}")
    for table in tables:
        count = len(data["tables"][table])
        print(f"   - {table}: {count} rows")


def load_json(db_path: Path, input_path: Path) -> None:
    """Load database from JSON file."""
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Clear existing data
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [row[0] for row in cursor.fetchall()]
    
    for table in tables:
        cursor.execute(f"DELETE FROM {table}")
    
    # Insert data from JSON
    for table, rows in data["tables"].items():
        if not rows:
            continue
        
        # Get columns from first row
        columns = list(rows[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        column_names = ', '.join(columns)
        
        insert_sql = f"INSERT INTO {table} ({column_names}) VALUES ({placeholders})"
        
        for row in rows:
            values = [row[col] for col in columns]
            cursor.execute(insert_sql, values)
    
    conn.commit()
    conn.close()
    
    print(f"✅ Loaded database from {input_path}")
    for table, rows in data["tables"].items():
        print(f"   - {table}: {len(rows)} rows")


def show_info(db_path: Path) -> None:
    """Show database information."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print(f"📊 Database: {db_path}")
    print(f"   Size: {db_path.stat().st_size / 1024:.1f} KB\n")
    
    # Get all tables
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    print("Tables:")
    total_rows = 0
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        total_rows += count
        print(f"   - {table}: {count} rows")
    
    print(f"\nTotal rows: {total_rows}")
    
    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="TrendCloset database dump/load utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s dump --format sql --output backup.sql
  %(prog)s dump --format json --output backup.json
  %(prog)s load --format sql --input backup.sql
  %(prog)s load --format json --input backup.json
  %(prog)s info
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Dump command
    dump_parser = subparsers.add_parser('dump', help='Dump database to file')
    dump_parser.add_argument(
        '--format', '-f',
        choices=['sql', 'json'],
        default='sql',
        help='Output format (default: sql)'
    )
    dump_parser.add_argument(
        '--output', '-o',
        required=True,
        help='Output file path'
    )
    
    # Load command
    load_parser = subparsers.add_parser('load', help='Load database from file')
    load_parser.add_argument(
        '--format', '-f',
        choices=['sql', 'json'],
        default='sql',
        help='Input format (default: sql)'
    )
    load_parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input file path'
    )
    
    # Info command
    subparsers.add_parser('info', help='Show database information')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        db_path = get_db_path()
        
        if args.command == 'dump':
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if args.format == 'sql':
                dump_sql(db_path, output_path)
            else:
                dump_json(db_path, output_path)
        
        elif args.command == 'load':
            input_path = Path(args.input)
            if not input_path.exists():
                print(f"❌ Error: Input file not found: {input_path}")
                sys.exit(1)
            
            # Confirm before overwriting
            response = input(f"⚠️  This will overwrite the current database ({db_path}). Continue? [y/N] ")
            if response.lower() != 'y':
                print("Cancelled.")
                sys.exit(0)
            
            if args.format == 'sql':
                load_sql(db_path, input_path)
            else:
                load_json(db_path, input_path)
        
        elif args.command == 'info':
            show_info(db_path)
    
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
