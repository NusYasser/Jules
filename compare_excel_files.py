import pandas as pd
import re
import numpy as np

def clean_string_column(series):
    """Cleans a pandas Series of strings."""
    if series.dtype == 'object':
        # Convert to string, strip whitespace, handle potential errors by filling NA
        return series.fillna('').astype(str).str.strip()
    return series

def is_likely_noise(name_str, desig_str=None, comp_str=None):
    """
    Heuristic to identify if a record (name, designation, company) is likely OCR noise or irrelevant.
    Returns True if it's likely noise, False otherwise.
    """
    if not isinstance(name_str, str) or not name_str.strip():
        return True  # Empty or non-string names are noise

    name_lower = name_str.lower()

    # 1. Length checks
    if len(name_str.strip()) < 2: # Single characters are almost always noise
        return True
    if len(name_str.strip()) == 2 and not re.search(r'[a-zA-Z]', name_str[0]) and not re.search(r'[a-zA-Z]', name_str[1]): # two symbols
        return True


    # 2. Specific noise patterns (UI elements, timestamps, symbols)
    #    (Added more patterns based on observed noise)
    noise_patterns = [
        r'\d{2}:\d{2}', r'\d{1,3}%', r'[®©™]', r'fl\b',
        r'messages', r'attendees', r'sessions', r'my agenda', r'maps', r'networking', r'more',
        r'http[s]?://', r'www\.', r'\.com', r'\.org', r'\.net',
        r'screenshot', r'image', r'file', r'edit', r'view', r'help',
        r'search attendees', r'attendees \(\d+\)',
        r'ill\s*o\s*<', # Pattern from "III O <"
        r'oe#', r'°@', r'\$\@\)', r'&\s*\d+', # Symbols from noisy examples
        r'ah\s*\d*\s*\d*\s*oe', # Pattern from "AH 8 9 Oe"
        r'unnamed', r'untitled', r'unknown',
        r'previous', r'next', r'page', r'select',
        r'notification', r'filter', r'sort by', r'camera', r'microphone'
    ]
    for pattern in noise_patterns:
        if re.search(pattern, name_lower):
            return True

    # Check combined string for UI patterns if available
    # Sometimes UI elements are split across fields by parse_text
    # This is an approximation
    combined_text_lower = name_lower
    if isinstance(desig_str, str) and desig_str.strip():
        combined_text_lower += " " + desig_str.lower()
    if isinstance(comp_str, str) and comp_str.strip():
        combined_text_lower += " " + comp_str.lower()

    ui_combo_patterns = [
        r"sessions my agenda maps networking more", # from "AH 8 9 Oe Sessions My Agenda Maps Networking More III O <"
        r"©\s*©\s*doo»" # from "ff © © Doo»" which was an early noise example
    ]
    for pattern in ui_combo_patterns:
        if re.search(pattern, combined_text_lower):
            return True


    # 3. Character type ratios
    alphanum_chars = sum(c.isalnum() for c in name_str)
    total_chars_no_space = sum(1 for c in name_str if not c.isspace())

    if total_chars_no_space == 0: return True # Only spaces

    if total_chars_no_space > 4 and (alphanum_chars / total_chars_no_space) < 0.5:
        return True

    letter_chars = sum(c.isalpha() for c in name_str)
    if total_chars_no_space > 0 and (letter_chars / total_chars_no_space) < 0.3:
        if re.search(r'[^\w\s\.\'-]', name_str): # Contains non-typical symbols
            return True

    # 4. Word structure (e.g., too many short words, or looks like a sentence fragment)
    words = name_str.split()
    if len(words) > 5 and all(len(w) < 4 for w in words): # Many very short words
        return True
    if len(words) == 1 and len(words[0]) > 25 and not re.search(r'\s', name_str): # Very long single "word" likely noise
        return True

    # 5. Name looks like a title/role (already partially handled by parse_text, but as a fallback)
    #    (Reduced this list as parse_text is primary filter for this)
    noisy_designations_as_names = ["manager", "director", "consultant", "engineer", "specialist", "administrator"]
    if name_lower in noisy_designations_as_names:
        return True

    # 6. If the name consists of mostly digits or symbols
    if total_chars_no_space > 0 and sum(c.isdigit() or not c.isalnum() for c in name_str if not c.isspace()) / total_chars_no_space > 0.7:
         # if >70% of non-space chars are digits or symbols
        return True

    # 7. Check for at least one word with reasonable length if name is multi-word
    if len(words) > 1:
        if not any(len(w) >= 2 for w in words if w.isalpha()): # No word part is at least 2 letters long
            return True
    elif len(words) == 1: # Single word name
        if not (len(name_str) >=2 and name_str.isalpha()): # Must be at least 2 chars and all alpha
             if not (len(name_str) > 2 and letter_chars/len(name_str) > 0.6): # Allow for names like "Dr. X" if mostly letters
                return True


    return False

def inspect_dataframe(df_name, df, full_head=False):
    """Prints shape, columns, and head of a DataFrame."""
    print(f"\n--- Inspecting DataFrame: {df_name} ---")
    if df is None:
        print("DataFrame is None.")
        return
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    if df.empty:
        print("DataFrame is empty.")
        return
    print("Head:")
    if full_head:
        print(df.to_string(index=False))
    else:
        print(df.head().to_string(index=False if not df.head().empty else True))


def main():
    generated_file = "output.xlsx"
    provided_file = "2.2.xlsx"

    df_generated = None
    df_provided = None

    print(f"Attempting to read generated file: {generated_file}")
    try:
        df_generated = pd.read_excel(generated_file, sheet_name=0, dtype=str).fillna('')
        print(f"Successfully read {generated_file}")
    except FileNotFoundError:
        print(f"Error: File not found - {generated_file}")
        return
    except Exception as e:
        print(f"Error reading {generated_file}: {e}")
        return

    print(f"\nAttempting to read provided file: {provided_file}")
    try:
        df_provided = pd.read_excel(provided_file, sheet_name=0, dtype=str).fillna('')
        print(f"Successfully read {provided_file}")
    except FileNotFoundError:
        print(f"Error: File not found - {provided_file}")
    except Exception as e:
        print(f"Error reading {provided_file}: {e}")

    # --- Preprocessing and Cleaning ---
    if df_generated is not None:
        df_generated.columns = [col.lower().strip() for col in df_generated.columns]
        for col in df_generated.columns:
            df_generated[col] = clean_string_column(df_generated[col])

        initial_row_count = len(df_generated)
        # Apply noise filter row-wise, passing all relevant fields to the heuristic
        noise_mask = df_generated.apply(lambda row: is_likely_noise(row.get('name'), row.get('designation'), row.get('company')), axis=1)
        df_generated = df_generated[~noise_mask].copy()
        rows_removed = initial_row_count - len(df_generated)
        print(f"\nRemoved {rows_removed} likely noise row(s) from the generated DataFrame using heuristics.")

        # Remove rows where essential fields (name, company) might be empty string after cleaning
        # (NaNs were already handled by fillna('') earlier, so checking for empty strings)
        df_generated = df_generated[df_generated['name'].str.strip().astype(bool) & df_generated['company'].str.strip().astype(bool)].copy()
        print(f"Removed {initial_row_count - len(df_generated) - rows_removed} more row(s) due to empty name/company after cleaning.")


    if df_provided is not None:
        df_provided.columns = [col.lower().strip() for col in df_provided.columns]
        for col in df_provided.columns:
            df_provided[col] = clean_string_column(df_provided[col])
        df_provided = df_provided[df_provided['name'].str.strip().astype(bool) & df_provided['company'].str.strip().astype(bool)].copy()


    inspect_dataframe("Generated (output.xlsx) - Cleaned", df_generated)
    inspect_dataframe("Provided (2.2.xlsx) - Cleaned", df_provided)

    if df_generated is None or df_provided is None:
        print("\nCannot perform comparison as one or both DataFrames could not be loaded/cleaned adequately.")
        return
    if df_generated.empty:
        print("\nGenerated DataFrame is empty after cleaning. No comparison possible.")
        return

    # --- Comparison ---
    df_generated['source_gen'] = True
    df_provided['source_prov'] = True

    merge_cols = ['name', 'designation', 'company']
    df_merged = pd.merge(df_generated, df_provided, on=merge_cols, how='outer', suffixes=('_gen', '_prov'))

    common_records = df_merged[df_merged['source_gen'].notna() & df_merged['source_prov'].notna()]
    unique_to_generated = df_merged[df_merged['source_gen'].notna() & df_merged['source_prov'].isna()]
    unique_to_provided = df_merged[df_merged['source_prov'].notna() & df_merged['source_gen'].isna()]

    print("\n\n--- Comparison Results ---")
    print(f"Total records in generated (cleaned): {len(df_generated)}")
    print(f"Total records in provided (cleaned): {len(df_provided)}")
    print(f"Number of common records (exact match on all fields): {len(common_records)}")
    print(f"Number of records unique to generated file: {len(unique_to_generated)}")
    print(f"Number of records unique to provided file: {len(unique_to_provided)}")

    if not common_records.empty:
        print("\n--- Examples of Common Records (first 5) ---")
        print(common_records[merge_cols].head().to_string(index=False))

    if not unique_to_generated.empty:
        print("\n--- Examples of Records Unique to Generated File (first 5) ---")
        print(unique_to_generated[merge_cols].head().to_string(index=False))

    if not unique_to_provided.empty:
        print("\n--- Examples of Records Unique to Provided File (first 5) ---")
        print(unique_to_provided[merge_cols].head().to_string(index=False))

if __name__ == "__main__":
    main()
