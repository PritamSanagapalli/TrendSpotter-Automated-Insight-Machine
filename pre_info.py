import pandas as pd
def summarize_df(df, output_prefix=None):
    print("=== DataFrame shape ===")
    print(df.shape)        
    print()
    
    print("=== DataFrame dtypes ===")
    print(df.dtypes)       
    print()

    print("=== Numeric summary (describe) ===")
    num_summary = df.describe()
    print(num_summary)
    print()

    print("=== Full summary (all columns) ===")
    full_summary = df.describe(include='all')
    print(full_summary)
    print()

    print("=== Missing values per column ===")
    missing = df.isna().sum().rename("na_count")
    missing_pct = (df.isna().mean() * 100).rename("na_pct")
    missing_summary = pd.concat([missing, missing_pct], axis=1)
    print(missing_summary)
    print()

    if output_prefix:
        num_summary.to_csv(f"{output_prefix}_numeric_summary.csv")
        full_summary.to_csv(f"{output_prefix}_full_summary.csv")
        missing_summary.to_csv(f"{output_prefix}_missing_summary.csv")
        print(f"Saved summaries to {output_prefix}_*.csv")
if __name__ == "__main__":
    df = pd.read_csv("your_data.csv")   
    summarize_df(df, output_prefix="report")