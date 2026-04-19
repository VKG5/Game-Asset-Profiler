# Advanced SQLite layer with indexing, UPSERT, and query helpers
import sqlite3
from contextlib import contextmanager
import shutil
import os

DB_NAME = "assets.db"

def set_db_path(new_path):
    global DB_NAME
    DB_NAME = new_path
    init_db()

def export_db(destination_path):
    if os.path.exists(DB_NAME):
        shutil.copy2(DB_NAME, destination_path)


@contextmanager
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        cursor = conn.cursor()

        # Main assets table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            path TEXT UNIQUE,
            type TEXT,
            size_bytes INTEGER,
            width INTEGER,
            height INTEGER,
            channels INTEGER,
            vram_estimate_mb REAL,
            insights TEXT,
            is_favorite INTEGER DEFAULT 0,
            last_scanned TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        # Indexes for fast querying (critical for large projects)
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_type ON assets(type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_vram ON assets(vram_estimate_mb)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_path ON assets(path)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_favorite ON assets(is_favorite)")

        conn.commit()


def upsert_asset(data):
    """
    Insert or update asset entry
    data = (path, type, size_bytes, width, height, channels, vram_mb)
    """
    with get_connection() as conn:
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO assets (path, type, size_bytes, width, height, channels, vram_estimate_mb)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(path) DO UPDATE SET
            type=excluded.type,
            size_bytes=excluded.size_bytes,
            width=excluded.width,
            height=excluded.height,
            channels=excluded.channels,
            vram_estimate_mb=excluded.vram_estimate_mb,
            last_scanned=CURRENT_TIMESTAMP
        """, data)

        conn.commit()


"""
Add column (only if you recreate DB or handle migration):
ALTER TABLE assets ADD COLUMN insights TEXT DEFAULT '';
"""
def upsert_asset_with_insights(conn, data):
    """
    data = (path, type, size_bytes, width, height, channels, vram_mb, insights_str)
    """
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO assets (path, type, size_bytes, width, height, channels, vram_estimate_mb, insights)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(path) DO UPDATE SET
        type=excluded.type,
        size_bytes=excluded.size_bytes,
        width=excluded.width,
        height=excluded.height,
        channels=excluded.channels,
        vram_estimate_mb=excluded.vram_estimate_mb,
        insights=excluded.insights,
        last_scanned=CURRENT_TIMESTAMP
    """, data)


# ========================= Query Helpers =========================
def fetch_assets(limit=1000, offset=0, sort_by="vram_estimate_mb", descending=True):
    order = "DESC" if descending else "ASC"

    query = f"""
    SELECT path, type, size_bytes, width, height, channels, vram_estimate_mb, insights, is_favorite
    FROM assets
    ORDER BY {sort_by} {order}
    LIMIT ? OFFSET ?
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, (limit, offset))
        return cursor.fetchall()


def filter_assets(min_vram=None, asset_type=None):
    conditions = []
    params = []

    if min_vram is not None:
        conditions.append("vram_estimate_mb >= ?")
        params.append(min_vram)

    if asset_type:
        conditions.append("type = ?")
        params.append(asset_type)

    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause

    query = f"""
    SELECT path, type, size_bytes, width, height, channels, vram_estimate_mb, insights, is_favorite
    FROM assets
    {where_clause}
    ORDER BY vram_estimate_mb DESC
    """

    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()


def fetch_flagged_assets():
    query = """
    SELECT path, insights
    FROM assets
    WHERE insights IS NOT NULL AND insights != ''
    ORDER BY path ASC
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()


def get_total_vram():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT SUM(vram_estimate_mb) FROM assets")
        result = cursor.fetchone()[0]
        return result if result else 0


def clear_database():
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assets")
        conn.commit()


def toggle_favorite(path):
    """Toggle favorite status for an asset"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT is_favorite FROM assets WHERE path = ?", (path,))
        result = cursor.fetchone()
        if result:
            current_favorite = result[0]
            new_favorite = 1 - current_favorite
            cursor.execute("UPDATE assets SET is_favorite = ? WHERE path = ?", (new_favorite, path))
            conn.commit()
            return new_favorite
        return 0


def set_favorite(path, is_favorite):
    """Set favorite status for an asset"""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE assets SET is_favorite = ? WHERE path = ?", (1 if is_favorite else 0, path))
        conn.commit()


def fetch_favorites():
    """Get all favorite assets"""
    query = """
    SELECT path, type, size_bytes, width, height, channels, vram_estimate_mb, insights, is_favorite
    FROM assets
    WHERE is_favorite = 1
    ORDER BY path ASC
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()


def get_database_statistics():
    """
    Returns dictionary with database statistics:
    {
        'total_assets': int,
        'total_vram_mb': float,
        'avg_vram_mb': float,
        'asset_type_counts': {'image': int, 'other': int, ...},
        'asset_count_with_insights': int
    }
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Total assets count
        cursor.execute("SELECT COUNT(*) FROM assets")
        total_assets = cursor.fetchone()[0]
        
        # Total and average VRAM
        cursor.execute("SELECT SUM(vram_estimate_mb), AVG(vram_estimate_mb) FROM assets")
        result = cursor.fetchone()
        total_vram_mb = result[0] if result[0] else 0.0
        avg_vram_mb = result[1] if result[1] else 0.0
        
        # Asset type breakdown
        cursor.execute("SELECT type, COUNT(*) FROM assets GROUP BY type")
        asset_type_counts = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Assets with insights
        cursor.execute("SELECT COUNT(*) FROM assets WHERE insights IS NOT NULL AND insights != ''")
        asset_count_with_insights = cursor.fetchone()[0]
        
        return {
            'total_assets': total_assets,
            'total_vram_mb': float(total_vram_mb),
            'avg_vram_mb': float(avg_vram_mb),
            'asset_type_counts': asset_type_counts,
            'asset_count_with_insights': asset_count_with_insights
        }


def search_assets_advanced(search_query=None, asset_type=None, min_vram=None, use_regex=False):
    """
    Advanced search with support for regex patterns and combined filters.
    
    Args:
        search_query: Search term (LIKE or regex pattern)
        asset_type: Filter by type (image, other, None for all)
        min_vram: Minimum VRAM in MB (None for all)
        use_regex: If True, treat search_query as regex pattern
    
    Returns:
        List of asset tuples: (path, type, size_bytes, width, height, channels, vram_mb, insights, is_favorite)
    """
    import re
    
    conditions = []
    params = []
    
    # Build base SQL query with filters
    if asset_type:
        conditions.append("type = ?")
        params.append(asset_type)
    
    if min_vram is not None:
        conditions.append("vram_estimate_mb >= ?")
        params.append(min_vram)
    
    where_clause = " AND ".join(conditions)
    if where_clause:
        where_clause = "WHERE " + where_clause
    
    query = f"""
    SELECT path, type, size_bytes, width, height, channels, vram_estimate_mb, insights, is_favorite
    FROM assets
    {where_clause}
    ORDER BY vram_estimate_mb DESC
    """
    
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        all_results = cursor.fetchall()
    
    # Apply search filter (either regex or LIKE)
    if not search_query:
        return all_results
    
    filtered_results = []
    search_query_lower = search_query.lower()
    
    if use_regex:
        try:
            pattern = re.compile(search_query_lower, re.IGNORECASE)
            for row in all_results:
                if pattern.search(row[0].lower()):  # Search in path
                    filtered_results.append(row)
        except re.error:
            # Fallback to LIKE on regex error
            for row in all_results:
                if search_query_lower in row[0].lower():
                    filtered_results.append(row)
    else:
        # Simple LIKE search
        for row in all_results:
            if search_query_lower in row[0].lower():
                filtered_results.append(row)
    
    return filtered_results


def fetch_all_assets():
    """
    Fetch all assets from the database for folder view.
    
    Returns:
        List of asset tuples: (path, type, size_bytes, width, height, channels, vram_mb, insights, is_favorite)
    """
    query = """
    SELECT path, type, size_bytes, width, height, channels, vram_estimate_mb, insights, is_favorite
    FROM assets
    ORDER BY path ASC
    """
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query)
        return cursor.fetchall()
