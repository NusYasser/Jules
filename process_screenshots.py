"""
Processes screenshot images to extract contact information (Name, Designation, Company),
and saves the aggregated data into an Excel spreadsheet.

This script performs the following steps:
1. Lists all screenshot files (matching 'screenshot_*.png') in the current directory.
2. For each screenshot:
    a. Extracts raw text using an OCR function (`extract_text_from_image.extract_text`).
    b. Parses the raw text to identify structured records (name, designation, company)
       using a parsing function (`parse_extracted_text.parse_text`).
    c. Handles errors during processing of individual files.
3. Aggregates all extracted records from all screenshots.
4. Saves the aggregated records into an Excel file named 'output.xlsx' using pandas.
"""

import os
import pandas as pd
from extract_text_from_image import extract_text
from parse_extracted_text import parse_text

def main():
    """
    Main function to process screenshots and generate an Excel report.
    """
    all_records = []
    screenshot_dir = "."  # Assuming screenshots are in the current directory

    # List files and filter for screenshots
    try:
        all_files = os.listdir(screenshot_dir)
    except OSError as e:
        print(f"Error listing directory {screenshot_dir}: {e}")
        return

    screenshot_files = [
        f for f in all_files if f.startswith("screenshot_") and f.endswith(".png")
    ]

    if not screenshot_files:
        print("No screenshot files (screenshot_*.png) found in the current directory.")
        return

    print(f"Found {len(screenshot_files)} screenshot(s) to process.")

    for filename in screenshot_files:
        filepath = os.path.join(screenshot_dir, filename)
        print(f"\nProcessing file: {filename}...")

        try:
            raw_text = extract_text(filepath)

            if raw_text and raw_text.strip():
                # print(f"--- Raw text from {filename} ---")
                # print(raw_text[:300] + "..." if len(raw_text) > 300 else raw_text) # Print snippet
                # print("--- End of raw text ---")

                parsed_records_from_file = parse_text(raw_text)

                if parsed_records_from_file:
                    all_records.extend(parsed_records_from_file)
                    print(f"Found {len(parsed_records_from_file)} record(s) in {filename}.")
                else:
                    print(f"No records found in {filename} after parsing.")
            else:
                print(f"No text extracted from {filename} or text was empty.")

        except Exception as e:
            print(f"An error occurred while processing file {filename}: {e}")
            # Optionally, log the error to a file or be more specific with exception handling

    # After processing all files
    if all_records:
        df = pd.DataFrame(all_records)
        # Ensure correct column order, though parse_text creates dicts with these keys
        df = df[['name', 'designation', 'company']]

        output_filename = "output_4_line_only.xlsx"
        try:
            df.to_excel(output_filename, index=False)
            print(f"\nSuccessfully saved {len(all_records)} record(s) to {output_filename}.")
        except Exception as e:
            print(f"Error saving data to Excel file {output_filename}: {e}")
    else:
        print("\nNo records were extracted from any of the screenshots.")

if __name__ == '__main__':
    main()
