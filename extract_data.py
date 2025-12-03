import os
import pandas as pd
import sqlite3
def load_file(path, **kwargs):
    _, ext = os.path.splitext(path)
    ext = ext.lower()
    if ext == '.csv':
        df = pd.read_csv(path, **kwargs)
        return df
    elif ext in ('.db', '.sqlite', '.sql'):
        conn = sqlite3.connect(path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        dfs = {}
        for tbl in tables:
            dfs[tbl] = pd.read_sql_query(f"SELECT * FROM {tbl}", conn)
        conn.close()
        return dfs
    else:
        raise ValueError(f"Unsupported file extension: {ext}")
if __name__ == "__main__":
    csv_path = "data/my_data.csv"
    sql_path = "data/my_db.sqlite"  
    try:
        df_csv = load_file(csv_path)
        print("CSV data:", df_csv.head())
    except Exception as e:
        print("Error loading CSV:", e)
    try:
        dict_dfs = load_file(sql_path)
        for tbl, df in dict_dfs.items():
            print(f"Table {tbl} — first 5 rows:")
            print(df.head())
    except Exception as e:
        print("Error loading SQL DB:", e)