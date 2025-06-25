import pandas as pd
import numpy as np

def preprocess_df(df, df_name):
    """Standardizes column names, strips whitespace, and removes rows with empty name/company."""
    expected_cols = ['name', 'designation', 'company']

    # Standardize column names to lowercase and strip whitespace
    df.columns = [col.lower().strip() for col in df.columns]

    # Ensure all expected columns exist, add as empty string column if not
    for col in expected_cols:
        if col not in df.columns:
            print(f"Column '{col}' not found in {df_name}. Adding as empty column.")
            df[col] = '' # Add as empty string

    # Fill NaN with empty strings before stripping, to handle mixed types gracefully
    for col in expected_cols:
        if col in df.columns: # Should always be true now
            df[col] = df[col].fillna('').astype(str).str.strip()

    # Remove rows where 'name' or 'company' are empty after stripping
    # Convert empty strings to NaN for easy dropping, then revert NaNs for consistency if needed (though not strictly for this step)
    df.replace('', np.nan, inplace=True)
    initial_rows = len(df)
    df.dropna(subset=['name', 'company'], inplace=True)
    rows_dropped = initial_rows - len(df)
    if rows_dropped > 0:
        print(f"Dropped {rows_dropped} rows from {df_name} due to empty 'name' or 'company'.")

    # Ensure only expected columns remain, in correct order (optional, but good for consistency)
    df = df[expected_cols]
    return df

def main():
    generated_file = "output.xlsx"
    provided_file = "2.2.xlsx"

    df_output = None
    df_expected = None

    print(f"Attempting to read generated file: {generated_file}")
    try:
        df_output = pd.read_excel(generated_file) # Let dtypes be inferred initially
        print(f"Successfully read {generated_file}")
    except FileNotFoundError:
        print(f"Error: File not found - {generated_file}")
    except Exception as e:
        print(f"Error reading {generated_file}: {e}")

    print(f"\nAttempting to read provided file: {provided_file}")
    try:
        df_expected = pd.read_excel(provided_file) # Let dtypes be inferred initially
        print(f"Successfully read {provided_file}")
    except FileNotFoundError:
        print(f"Error: File not found - {provided_file}")
    except Exception as e:
        print(f"Error reading {provided_file}: {e}")

    if df_output is None and df_expected is None:
        print("Both files could not be read. Exiting.")
        return

    # Preprocessing and Cleaning
    if df_output is not None:
        print("\nPreprocessing df_output...")
        df_output = preprocess_df(df_output, "df_output")
    else:
        # Create an empty df with expected columns if file was missing, for graceful merge
        print(f"{generated_file} not loaded. Using empty DataFrame for output.")
        df_output = pd.DataFrame(columns=['name', 'designation', 'company'])


    if df_expected is not None:
        print("\nPreprocessing df_expected...")
        df_expected = preprocess_df(df_expected, "df_expected")
    else:
        print(f"{provided_file} not loaded. Using empty DataFrame for expected.")
        df_expected = pd.DataFrame(columns=['name', 'designation', 'company'])


    # Comparison
    print(f"\n--- Shape of cleaned df_output: {df_output.shape} ---")
    print(f"--- Shape of cleaned df_expected: {df_expected.shape} ---")

    # Add source indicators for merge
    df_output['source'] = 'output_only'
    df_expected['source'] = 'expected_only'

    # Outer merge
    df_merged = pd.merge(df_output, df_expected, on=['name', 'designation', 'company'], how='outer', suffixes=('_output', '_expected'))

    # Determine common and unique records
    df_merged['source_output'] = df_merged['source_output'].fillna(pd.NA)
    df_merged['source_expected'] = df_merged['source_expected'].fillna(pd.NA)

    common_records_mask = df_merged['source_output'].notna() & df_merged['source_expected'].notna()
    output_only_mask = df_merged['source_output'].notna() & df_merged['source_expected'].isna()
    expected_only_mask = df_merged['source_output'].isna() & df_merged['source_expected'].notna()

    num_common = common_records_mask.sum()
    num_output_only = output_only_mask.sum()
    num_expected_only = expected_only_mask.sum()

    print("\n--- Comparison Report ---")
    print(f"Number of records only in df_output: {num_output_only}")
    print(f"Number of records only in df_expected: {num_expected_only}")
    print(f"Number of common records (exact match on all key fields): {num_common}")

    if num_output_only > 0:
        print("\n--- First 5 records unique to df_output ---")
        print(df_merged[output_only_mask][['name', 'designation', 'company']].head().to_string(index=False))

    if num_common > 0:
        print("\n--- First 5 common records ---")
        print(df_merged[common_records_mask][['name', 'designation', 'company']].head().to_string(index=False))

if __name__ == "__main__":
    main()
