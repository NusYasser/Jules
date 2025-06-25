import re

# --- Global Keyword Definitions ---
# These lists were fairly stable in the target version
COMPANY_KEYWORDS_LOWER = sorted(list(set([
    "inc.", "inc", "ltd.", "ltd", "llc", "corp.", "corp", "solutions", "group", "technologies",
    "services", "consulting", "university", "bank", "company", "co.", "co", "gmbh", "s.a.", "s.l.",
    "firm", "studio", "enterprises", "industries", "systems", "global", "international", "plc",
    "associates", "partners", "holdings", "ventures", "logistics", "manufacturing", "llp", "sarl",
    "foundation", "institute", "center", "bureau", "agency", "department", "press", "sas",
    "foods", "pharma", "motors", "electric", "data", "media", "capital", "advisors", "kft",
    "labs", "networks", "telecom", "energy", "health", "financial", "security", "ab", "oy",
    "properties", "realty", "construction", "design", "software", "analytics", "cloud",
    ".com", ".org", ".net", ".io", ".ai", ".gov", ".edu", ".eu", ".us", ".uk", ".de", ".fr",
    "& son", "& sons", "dept", "dept."
])))

TITLE_KEYWORDS_LOWER = sorted(list(set([
    "head", "manager", "director", "chief", "lead", "vp", "president", "senior", "junior", "sr.", "jr.",
    "officer", "engineer", "specialist", "consultant", "analyst", "representative", "administrator",
    "executive", "coordinator", "supervisor", "principal", "associate", "fellow", "architect",
    "phd", "md", "mba", "cpa", "cto", "ceo", "cfo", "coo", "cio", "cso", "ciso", "chro", "cmo",
    "founder", "partner", "advisor", "chair", "member", "dean", "professor", # "dr." handled by prefixes
    "developer", "designer", "planner", "strategist", "scientist", "researcher", "recruiter",
    "support", "assistant", "secretary", "treasurer", "controller", "auditor", "broker",
    "agent", "evp", "svp", "avp", "staff", "faculty", "technician", "clerk"
])))

COMMON_NAME_PREFIXES_LOWER = ["dr.", "dr", "prof.", "prof", "mr.", "mrs.", "ms.", "miss"]
# This list was used in is_plausible_name_line to reject single word company-like names
SINGLE_WORD_NON_NAME_LOWER = ["solutions", "technologies", "systems", "services", "associates", "consulting", "industries", "ventures", "global", "international", "analytics", "software", "corporation", "incorporated", "limited", "faddom", "group", "inc", "corp", "ltd", "llc", "company"]


# --- Helper Functions (from the version at end of Subtask 7 / start of Subtask 8) ---

def _line_contains_keyword_words(line_lower, keywords):
    words = line_lower.split()
    return any(kw in words for kw in keywords)

def is_likely_company_line(line, for_name_check=False): # for_name_check means stricter for skipping lines[i]
    line_lower = line.lower()
    words = line_lower.split()
    if not line.strip(): return False

    # ALL CAPS check: more likely company if contains company keyword or is short (like IBM)
    if line.isupper() and len(words) <= 3 and len(line.replace(" ", "")) > 1:
        if any(ckw in words for ckw in COMPANY_KEYWORDS_LOWER): return True
        if len(words) == 1 and line_lower not in TITLE_KEYWORDS_LOWER : return True # Single all-caps word is company if not a title like "CEO"

    # Suffixes and exact matches
    for kw in COMPANY_KEYWORDS_LOWER:
        if line_lower.endswith(f" {kw.lower()}") or line_lower == kw.lower(): return True
        if kw.startswith(".") and kw in line_lower: return True # TLDs

    if " & " in line and any(kw_s in words for kw_s in ["son", "sons", "associates", "partners", "co", "company"]): return True

    # Single word, title case, from a list of common business types
    if len(words) == 1 and line[0].isupper() and line_lower in SINGLE_WORD_NON_NAME_LOWER : return True
    if len(words) == 1 and line[0].isupper() and line_lower.endswith('s') and line_lower[:-1] in SINGLE_WORD_NON_NAME_LOWER: return True


    if for_name_check: # Stricter for initial line check
        strong_company_substrings = [" inc", " ltd", " llc", " corp", " gmbh", " university", " group", " solutions", " systems", " technologies", " bank", " consulting"]
        if any(sub in line_lower for sub in strong_company_substrings): return True
    else: # More lenient for validating 3rd/4th line of a block
        general_company_kws = ["solutions", "systems", "services", "data", "media", "cloud", "analytics", "ventures", "group", "firm", "studio"]
        if any(gckw in words for gckw in general_company_kws) and len(words) <= 3: return True
        # Generic company name like "Short Comp"
        if len(words) <= 2 and line[0].isupper() and not is_likely_title_line(line, for_name_check=False) and not (len(words)==2 and all(w[0].isupper() for w in words)): # Avoid "First Last"
            return True
    return False

def is_likely_title_line(line, for_name_check=False):
    line_lower = line.lower()
    words = line_lower.split()
    if not line.strip(): return False

    for prefix in COMMON_NAME_PREFIXES_LOWER: # e.g. "Dr. Smith" is not a title line, but "Dr. Head of Stuff" is
        if line_lower.startswith(prefix + " "):
            rest_of_line = line[len(prefix)+1:].strip().lower()
            if not rest_of_line or len(rest_of_line.split()) < 2 or _line_contains_keyword_words(rest_of_line, TITLE_KEYWORDS_LOWER):
                return True

    if _line_contains_keyword_words(line_lower, TITLE_KEYWORDS_LOWER): return True

    first_word_is_title_indicator = words[0] in ["head", "vp", "chief", "lead", "sr", "sr.", "jr", "jr.", "senior", "junior", "principal", "group", "svp", "evp", "avp", "global", "product", "project", "account", "strategy", "operations", "marketing", "sales", "finance", "human", "customer", "technical", "digital", "data", "software", "solution", "security"]
    if first_word_is_title_indicator and len(words) >= 2 and len(words) <= 5: return True # "Senior Manager", "Head of Marketing"
    if "," in line and _line_contains_keyword_words(line_lower.split(',')[0], TITLE_KEYWORDS_LOWER): return True

    # If for_name_check, be more aggressive if it contains any title keyword prominently
    if for_name_check and any(kw in line_lower for kw in TITLE_KEYWORDS_LOWER):
        if any(line_lower.startswith(kw) for kw in TITLE_KEYWORDS_LOWER if len(kw)>2) or len(words) <=3 :
            return True
    return False

def is_plausible_name_line(line): # This is the version from Subtask 7/8 boundary
    if not line.strip() or len(line.strip()) < 2 : return False

    original_line = line
    line_for_checks = line
    line_lower = line.lower()

    for prefix in COMMON_NAME_PREFIXES_LOWER:
        if line_lower.startswith(prefix + " "):
            potential_name_part = line[len(prefix)+1:].strip()
            if len(potential_name_part) >= 2 :
                line_for_checks = potential_name_part # Check the rest
                line_lower = line_for_checks.lower() # update lower version
                break
        elif line_lower == prefix: return False # Line is ONLY "Dr."

    if not line_for_checks.strip() or len(line_for_checks.strip()) < 2: return False

    # Use stricter checks for company/title when evaluating if this line IS a name
    if is_likely_company_line(original_line, for_name_check=True): return False
    if is_likely_title_line(original_line, for_name_check=True): return False

    words = line_for_checks.split()
    num_words = len(words)

    # Names are usually 1-4 words (e.g. "John Doe", "Jean-Luc Picard", "Dr. J. R. Smith")
    # The original_line word count should be used if prefix was stripped for this check
    original_words = original_line.split()
    original_num_words = len(original_words)
    if not (1 <= original_num_words <= 5): return False # Allow up to 5 for "Dr. First M. Last Name"

    # Name should not be all lowercase for multi-word names (allow for single short names like "jo")
    if line_for_checks.islower() and (num_words > 1 or len(line_for_checks) > 3):
         return False # "john smith" is not plausible if OCR is good

    # All uppercase names are plausible if short and not company-like (e.g. "JOHN DOE", "CJ")
    if line_for_checks.isupper():
        if num_words > 3 : return False # "A VERY LONG ALL CAPS NAME" is likely not a person
        # "JOHN DOE" should pass. is_likely_company_line(for_name_check=True) should ensure it's not "BIG CORP INC"

    # Symbol check (allow '.', '-' for names like "J.P.", "Smith-Jones", "'")
    valid_char_count = sum(1 for char in line_for_checks if char.isalnum() or char.isspace() or char in "'-.")
    if len(line_for_checks) > 0 and valid_char_count / len(line_for_checks) < 0.8: return False # High proportion of other symbols
    if line_for_checks.count('@') > 0 : return False # No emails

    # Digit check (allow "Name2" or "Name III" but not "Name123" or many digits)
    digit_count = sum(c.isdigit() for c in line_for_checks)
    if digit_count > 1 and not (re.search(r'[IVXLCDM]+$', words[-1], re.I) and len(words[-1]) <=3 ): return False
    if digit_count == 1 and not words[-1][-1].isdigit() and not (re.search(r'[IVXLCDM]+$', words[-1], re.I) and len(words[-1]) <=3 ): return False

    # Check for common junk words that might be plausible otherwise
    if num_words <= 2 and line_for_checks.lower() in ["profile", "contact", "details", "name", "title", "company", "other", "solutions", "services", "systems", "untitled", "unknown", "select", "next", "previous", "page"]:
        return False

    # Single word name should be mostly alpha or an initial like "J."
    if num_words == 1:
        if len(line_for_checks) < 2 : return False
        is_initial_dot = (len(line_for_checks) == 2 and line_for_checks[1] == '.' and line_for_checks[0].isalpha())
        if not (line_for_checks.isalpha() or is_initial_dot):
            if sum(c.isalpha() for c in line_for_checks) / len(line_for_checks) < 0.6: return False

    # A name usually has at least one capitalized word (unless it's a very short lowercase name like "jo")
    if not any(c.isupper() for c in line_for_checks if c.isalpha()) and len(line_for_checks) > 3 and " " in line_for_checks:
        return False
    return True


# --- Main Parsing Function (Reverted to logic from end of Subtask 7/start of Subtask 8) ---
def parse_text(text_content):
    parsed_records = []
    if not text_content: return parsed_records
    lines = [line.strip() for line in text_content.splitlines() if line.strip()]

    i = 0
    while i < len(lines):
        block_parsed_in_iteration = False
        name_candidate = lines[i]

        # 1. Skip current line if it's not a plausible person's name
        if not is_plausible_name_line(name_candidate):
            i += 1
            continue

        # 2. Try to parse a 4-line block
        if i + 3 < len(lines):
            potential_desig_line1 = lines[i+1]
            potential_desig_line2 = lines[i+2]
            potential_company_for_4line = lines[i+3]

            # Condition: line[i+2] should NOT be a company (it's part of designation)
            # AND line[i+3] SHOULD be a company (using lenient company check)
            # AND line[i+3] should NOT be a new plausible name for a subsequent record
            if (not is_likely_company_line(potential_desig_line2, for_name_check=False) and # lenient check for d2
                is_likely_company_line(potential_company_for_4line, for_name_check=False) and # lenient check for company
                not is_plausible_name_line(potential_company_for_4line) and
                not is_likely_title_line(potential_desig_line1, for_name_check=True) and # d1 not a title
                not is_likely_title_line(potential_desig_line2, for_name_check=True) # d2 not a title
                ):
                parsed_records.append({
                    'name': name_candidate,
                    'designation': potential_desig_line1 + " " + potential_desig_line2,
                    'company': potential_company_for_4line
                })
                i += 4
                block_parsed_in_iteration = True

        if block_parsed_in_iteration: continue

        # 3. Try to parse a 3-line block
        if i + 2 < len(lines):
            potential_desig = lines[i+1]
            potential_company = lines[i+2]

            # Condition: line[i+2] (potential_company) SHOULD be a company (lenient check).
            # AND line[i+1] (potential_desig) should NOT be a plausible new name or a company itself.
            # AND line[i+2] (potential_company) should NOT be a plausible new name.
            if (is_likely_company_line(potential_company, for_name_check=False) and
                not is_plausible_name_line(potential_desig) and
                not is_likely_company_line(potential_desig, for_name_check=True) and
                not is_plausible_name_line(potential_company) ):
                parsed_records.append({
                    'name': name_candidate,
                    'designation': potential_desig,
                    'company': potential_company
                })
                i += 3
                block_parsed_in_iteration = True

        if block_parsed_in_iteration: continue
        i += 1

    return parsed_records

# --- Test Cases (Subset for validation of this specific restored version) ---
if __name__ == '__main__':
    # This test suite is for self-testing the restored version.
    # It reflects the expected state of TC1-18 and specific challenges.
    tests = {
        "TC1_Std_3Line": ("John Doe\nSoftware Engineer\nTech Solutions Inc.", [{'name': 'John Doe', 'designation': 'Software Engineer', 'company': 'Tech Solutions Inc.'}]),
        "TC2_Std_4Line": ("Jane Smith\nSenior Technical Program\nManager\nInnovate Corp", [{'name': 'Jane Smith', 'designation': 'Senior Technical Program Manager', 'company': 'Innovate Corp'}]),
        "TC3_Mixed_3_4": ("Peter Jones\nProject Lead\nBuildIt LLC\nAlice Brown\nChief Executive\nOfficer\nEnterprise Co.", [{'name': 'Peter Jones', 'designation': 'Project Lead', 'company': 'BuildIt LLC'}, {'name': 'Alice Brown', 'designation': 'Chief Executive Officer', 'company': 'Enterprise Co.'}]),
        "TC5_Skip_Initial_Title": ("Head of Operations\nGlobal Corp\nEmily White\nUX Designer\nCreative Studio", [{'name': 'Emily White', 'designation': 'UX Designer', 'company': 'Creative Studio'}]),
        "TC7_Short_3Line": ("Short Name\nShort Desig\nShort Comp", [{'name': 'Short Name', 'designation': 'Short Desig', 'company': 'Short Comp'}]),
        "TC12_Two_3Line": ("First Person\nFirst Role\nFirst Company\nSecond Person\nSecond Role\nSecond Company", [{'name': 'First Person', 'designation': 'First Role', 'company': 'First Company'}, {'name': 'Second Person', 'designation': 'Second Role', 'company': 'Second Company'}]),
        "TC17_Ford_Prefect": ("Ford Prefect\nResearcher\nBetelgeuse Corp", [{'name': 'Ford Prefect', 'designation': 'Researcher', 'company': 'Betelgeuse Corp'}]),
        "TC18_Solutions_Start_Original_Fail": ("Solutions\nAnother Line\nYet Another Line\nThis Is A Name\nThis Is A Desig\nThis Is A Comp Inc.", [{'name': 'This Is A Name', 'designation': 'This Is A Desig', 'company': 'This Is A Comp Inc.'}]), # Expected fail or different parse
        "TC22_AllCapsCompany_Skip": ("GLOBAL MEGA CORP INC\nAlice Wonderland\nChief Visionary Officer\nUniverse Systems", [{'name': 'Alice Wonderland', 'designation': 'Chief Visionary Officer', 'company': 'Universe Systems'}]),
        "TC24_AIR_FRANCE_Targeted": ("AIR FRANCE\nOlivier QUEVAL\nDirector Systems and Integration\nAir France Operations", [{'name': 'Olivier QUEVAL', 'designation': 'Director Systems and Integration', 'company': 'Air France Operations'}]),
        "TC25_Faddom_Targeted": ("Faddom\nOla Norlander\nSenior advisor\nOla Norlander inc.", [{'name': 'Ola Norlander', 'designation': 'Senior advisor', 'company': 'Ola Norlander inc.'}]),
        "TC28_Dr_Prefix_Targeted": ("Dr. Emily Carter\nChief Scientist\nQuantum Innovations", [{'name': 'Dr. Emily Carter', 'designation': 'Chief Scientist', 'company': 'Quantum Innovations'}]),
        "TC29_JOHN_DOE_Targeted": ("JOHN DOE\nSoftware Engineer\nTech Solutions Inc.", [{'name': 'JOHN DOE', 'designation': 'Software Engineer', 'company': 'Tech Solutions Inc.'}])
    }

    passed_count = 0
    failed_count = 0
    print("Running self-test suite for restored parser logic...")
    for name, (input_str, expected_output) in tests.items():
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
        print("All self-test cases PASSED.")
    else:
        print(f"WARNING: {failed_count} self-test cases FAILED. Review logic before proceeding.")
