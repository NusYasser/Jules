import pandas as pd

def main():
    filename = "output_4_line_only.xlsx"
    df = None

    print(f"Attempting to read file: {filename}")
    try:
        df = pd.read_excel(filename)
        print(f"Successfully read {filename}")
    except FileNotFoundError:
        print(f"Error: File not found - {filename}")
        return
    except Exception as e:
        print(f"Error reading {filename}: {e}")
        return

    if df is None:
        print("DataFrame could not be loaded.")
        return

    num_records = len(df)
    print(f"\nTotal number of records found: {num_records}")

    if num_records == 0:
        print("No records to display.")
        return

    print("\n--- First 15 records ---")
    print(df.head(15).to_string())

    if num_records > 15:
        print("\n--- Last 15 records ---")
        print(df.tail(15).to_string())

    if num_records > 30:
        # Calculate middle start index, ensuring it doesn't go out of bounds for tail.
        # e.g. if 45 records, middle 15 could be from index 15 to 29.
        # (0-14 are first 15, 15-29 are next 15, 30-44 are last 15)
        middle_start = 15
        middle_end = middle_start + 15
        if middle_end > num_records -15 : # Avoid overlap with tail if dataset isn't large enough
            middle_end = num_records -15
            if middle_start >= middle_end: # if not enough records for a distinct middle set
                 print("\nNot enough records for a distinct middle sample of 15 without overlapping first/last.")
                 return


        print(f"\n--- Middle 15 records (from index {middle_start} to {middle_end-1}) ---")
        print(df.iloc[middle_start:middle_end].to_string())


if __name__ == "__main__":
    main()
