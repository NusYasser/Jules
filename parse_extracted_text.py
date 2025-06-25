import re

# Junk keywords to filter out potential names/companies
JUNK_KEYWORDS_LOWER = [
    "continued on", "page of", "screenshot by", "search results", "profile details",
    "contact information", "message", "connect", "skip", "attendees", "sessions",
    "agenda", "networking", "settings", "filter", "sort by", "next page", "previous page",
    "advertisement", "sponsored by", "terms of service", "privacy policy", "copyright",
    "select all", "deselect", "edit profile", "view profile", "share", "download", "print",
    "log out", "sign in", "register", "help center", "faq", "support", "feedback"
]

TITLES_AS_JUNK_LOWER = ["ceo", "cto", "cfo", "coo", "cio", "manager", "director", "president", "vice president", "officer", "engineer", "consultant", "specialist", "analyst", "representative", "executive"]


COMPANY_SUFFIXES_LOWER = [ # Used for endswith checks, expect leading space
    " inc", " ltd", " llc", " corp", " gmbh", " s.a.", " co", " company",
    ".com", ".org", ".net", ".io", ".ai", ".co.uk"
]
COMPANY_SUFFIXES_EXACT_LOWER = [ # Used for exact matches, no leading/trailing spaces needed
    "inc", "ltd", "llc", "corp", "gmbh", "s.a.", "co"
]
# Add dot versions for exact matches too
COMPANY_SUFFIXES_EXACT_LOWER.extend([s + "." for s in COMPANY_SUFFIXES_EXACT_LOWER if not s.endswith(".")])


def contains_junk(text_lower, junk_list):
    """Checks if text contains any junk keyword/phrase."""
    return any(junk in text_lower for junk in junk_list)

def check_alnum_ratio(text, threshold=0.4):
    if not text: return False # Empty string fails
    # ZeroDivisionError if text has no characters after potential stripping, though input lines are pre-stripped
    if len(text) == 0: return False
    return (sum(c.isalnum() for c in text) / len(text)) >= threshold

def parse_text(text_content):
    parsed_records = []
    if not text_content:
        return parsed_records

    lines = [line.strip() for line in text_content.splitlines() if line.strip()]

    i = 0
    while i <= len(lines) - 4:
        name_line = lines[i]
        d1_line = lines[i+1]
        d2_line = lines[i+2]
        company_line = lines[i+3]

        name_lower = name_line.lower()
        company_lower = company_line.lower()

        # --- Perform all checks ---
        name_ok = True
        if contains_junk(name_lower, JUNK_KEYWORDS_LOWER): name_ok = False
        if name_ok and name_lower in TITLES_AS_JUNK_LOWER: name_ok = False
        if name_ok and ((len(name_line) < 3 and not name_line.isupper()) or (len(name_line) < 2 and name_line.isupper())): name_ok = False
        if name_ok and any(name_lower.endswith(suffix) for suffix in COMPANY_SUFFIXES_LOWER): name_ok = False
        if name_ok and name_lower in COMPANY_SUFFIXES_EXACT_LOWER: name_ok = False
        if name_ok and (name_line.isdigit() or not check_alnum_ratio(name_line)): name_ok = False

        d1_ok = True
        if contains_junk(d1_line.lower(), JUNK_KEYWORDS_LOWER): d1_ok = False
        if d1_ok and len(d1_line) < 2: d1_ok = False
        if d1_ok and (d1_line.lower() in TITLES_AS_JUNK_LOWER and len(d1_line.split())==1): d1_ok = False
        if d1_ok and any(d1_line.lower().endswith(suffix) for suffix in COMPANY_SUFFIXES_LOWER): d1_ok = False
        if d1_ok and d1_line.lower() in COMPANY_SUFFIXES_EXACT_LOWER: d1_ok = False

        d2_ok = True
        if contains_junk(d2_line.lower(), JUNK_KEYWORDS_LOWER): d2_ok = False
        if d2_ok and len(d2_line) < 2: d2_ok = False
        if d2_ok and (d2_line.lower() in TITLES_AS_JUNK_LOWER and len(d2_line.split())==1): d2_ok = False
        if d2_ok and any(d2_line.lower().endswith(suffix) for suffix in COMPANY_SUFFIXES_LOWER): d2_ok = False
        if d2_ok and d2_line.lower() in COMPANY_SUFFIXES_EXACT_LOWER: d2_ok = False

        company_ok = True
        if contains_junk(company_lower, JUNK_KEYWORDS_LOWER): company_ok = False
        has_suffix = any(company_lower.endswith(suffix) for suffix in COMPANY_SUFFIXES_LOWER)
        is_short_caps = company_line.isupper() and len(company_line) >= 2 and len(company_line) <=4
        if company_ok and not has_suffix and not is_short_caps and len(company_line) < 4 : company_ok = False
        if company_ok and (company_line.isdigit() or not check_alnum_ratio(company_line)): company_ok = False

        # Advanced check for company looking like a new person's name
        adv_company_check_pass = True # Assume it passes unless proven otherwise
        company_words = company_line.split()
        if len(company_words) >= 2 and len(company_words) <=3 and \
           all(w and w[0].isupper() for w in company_words) and \
           not has_suffix and \
           not contains_junk(company_lower, JUNK_KEYWORDS_LOWER) and \
           not any(cw.lower() in COMPANY_SUFFIXES_EXACT_LOWER for cw in company_words) and \
           not any(cw.lower() in TITLES_AS_JUNK_LOWER for cw in company_words):
            if i + 4 < len(lines):
                line_i_plus_4 = lines[i+4].lower()
                # If next line looks like a designation (not junk, not company, reasonable length/structure)
                if not contains_junk(line_i_plus_4, JUNK_KEYWORDS_LOWER) and \
                   not any(line_i_plus_4.endswith(suffix) for suffix in COMPANY_SUFFIXES_LOWER) and \
                   len(line_i_plus_4.split()) <= 3 and len(line_i_plus_4) > 2 and \
                   line_i_plus_4 not in COMPANY_SUFFIXES_EXACT_LOWER and \
                   line_i_plus_4 not in TITLES_AS_JUNK_LOWER :
                    adv_company_check_pass = False # Invalidates current block: company is likely a new name

        if name_ok and d1_ok and d2_ok and company_ok and adv_company_check_pass:
            designation = d1_line + " " + d2_line
            parsed_records.append({'name': name_line, 'designation': designation, 'company': company_line})
            i += 4
        else:
            i += 1

    return parsed_records

if __name__ == '__main__':
    tests = [
        {
            "name": "TC1_Clear_4_Line",
            "input": """John B. Doe
Vice President
Marketing & Sales
Acme Innovations Ltd.""",
            "expected": [{'name': 'John B. Doe', 'designation': 'Vice President Marketing & Sales', 'company': 'Acme Innovations Ltd.'}]
        },
        {
            "name": "TC2_Not_4_Line_Sequence",
            "input": """Jane Smith
CEO
Beta Corp
Another Person
Director""",
            "expected": []
        },
        {
            "name": "TC3_Filter_Name_Junk",
            "input": """Search Results
For Your Query
Please Review
System Generated""",
            "expected": []
        },
        {
            "name": "TC4_Filter_Company_Junk",
            "input": """Valid Name
Valid Designation Line 1
Valid Designation Line 2
Contact Information""",
            "expected": []
        },
        {
            "name": "TC5_5_Line_Sequence_Valid_First_4",
            "input": """Peter Jones
Chief Technology
Officer (CTO)
Tech Solutions Inc.
Some other text""",
            "expected": [{'name': 'Peter Jones', 'designation': 'Chief Technology Officer (CTO)', 'company': 'Tech Solutions Inc.'}]
        },
        {
            "name": "TC6_Fewer_Than_4_Lines",
            "input": """Line 1
Line 2
Line 3""",
            "expected": []
        },
        {
            "name": "TC7_Name_Is_Company_Suffix",
            "input": """Inc.
Some Designation
Some Other Desig
Some Company""",
            "expected": []
        },
        {
            "name": "TC8_Company_Looks_Like_New_Name",
            "input": """Real Person Name
Senior Analyst
Special Projects
Next Person Name
Associate Director""",
            "expected": []
        },
        {
            "name": "TC9_Very_Short_Name_Allowed_If_Caps",
            "input": """CJ
Chief Janitor
Department of Cleanliness
Big Building Corp""",
            "expected": [{'name': 'CJ', 'designation': 'Chief Janitor Department of Cleanliness', 'company': 'Big Building Corp'}]
        },
        {
            "name": "TC10_Very_Short_Name_Filtered_If_Not_Caps",
            "input": """Jo
Chief Joker
Department of Fun
Big Show LLC""",
            "expected": []
        },
        {
            "name": "TC11_Multiple_4_Line_Blocks",
            "input": """First Guy
Top Manager
Strategy & Planning
Future Corp.
Second Lady
VP Operations
Logistics Department
Global Transport Co
Junk Line
Another Junk""",
            "expected": [
                {'name': 'First Guy', 'designation': 'Top Manager Strategy & Planning', 'company': 'Future Corp.'},
                {'name': 'Second Lady', 'designation': 'VP Operations Logistics Department', 'company': 'Global Transport Co'}
            ]
        },
         {
            "name": "TC12_Name_Is_Digits",
            "input": """1234567
Some Designation
Some Other Desig
Some Company""",
            "expected": []
        },
        {
            "name": "TC13_Name_Is_CEO_title",
            "input": """CEO
Some Person Name
Some Other Desig
Some Company""",
            "expected": []
        }

    ]

    passed_count = 0
    failed_count = 0
    print("Running test suite for 4-line block extraction (final polish)...")
    for test in tests:
        name = test["name"]
        input_str = test["input"]
        expected_output = test["expected"]

        actual_output = parse_text(input_str)

        if actual_output == expected_output:
            passed_count +=1
        else:
            print(f"--- {name} ---")
            print(f"Status: FAIL")
            print(f"  Input:\n{input_str}")
            print(f"  Actual Output:\n{actual_output}")
            print(f"  Expected Output:\n{expected_output}")
            print("")
            failed_count +=1

    print(f"\n--- Summary ---")
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")

    if failed_count == 0:
        print("All test cases PASSED.")
    else:
        print(f"WARNING: {failed_count} test cases FAILED.")
