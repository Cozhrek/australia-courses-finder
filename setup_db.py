"""
Convert CRICOS XLSX data to SQLite database.
Run once: python setup_db.py
"""
import sqlite3
import pandas as pd
import os
import sys

XLSX_PATH = r"C:\Users\putra\Downloads\cricos-providers-courses-and-locations-as-at-2026-3-2-11-34-49.xlsx"
DB_PATH = "courses.db"


def clean_str(val):
    if pd.isna(val):
        return None
    return str(val).strip()


def clean_num(val):
    if pd.isna(val):
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def main():
    if not os.path.exists(XLSX_PATH):
        print(f"ERROR: XLSX file not found at:\n{XLSX_PATH}")
        sys.exit(1)

    print("Reading Excel file... (this may take 30-60 seconds)")

    df_inst = pd.read_excel(XLSX_PATH, sheet_name="Institutions", header=2)
    df_courses = pd.read_excel(XLSX_PATH, sheet_name="Courses", header=2)
    df_locs = pd.read_excel(XLSX_PATH, sheet_name="Locations", header=2)
    df_cl = pd.read_excel(XLSX_PATH, sheet_name="Course Locations", header=2)

    print(f"  Institutions: {len(df_inst)} rows")
    print(f"  Courses: {len(df_courses)} rows")
    print(f"  Locations: {len(df_locs)} rows")
    print(f"  Course Locations: {len(df_cl)} rows")

    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    c = conn.cursor()

    c.executescript("""
        DROP TABLE IF EXISTS institutions;
        DROP TABLE IF EXISTS courses;
        DROP TABLE IF EXISTS locations;
        DROP TABLE IF EXISTS course_locations;

        CREATE TABLE institutions (
            cricos_provider_code TEXT PRIMARY KEY,
            trading_name TEXT,
            institution_name TEXT,
            institution_type TEXT,
            institution_capacity INTEGER,
            website TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            postcode TEXT
        );

        CREATE TABLE courses (
            cricos_course_code TEXT PRIMARY KEY,
            cricos_provider_code TEXT,
            institution_name TEXT,
            course_name TEXT,
            vet_national_code TEXT,
            dual_qualification TEXT,
            field_broad TEXT,
            field_narrow TEXT,
            field_detailed TEXT,
            course_level TEXT,
            foundation_studies TEXT,
            work_component TEXT,
            course_language TEXT,
            duration_weeks REAL,
            tuition_fee REAL,
            non_tuition_fee REAL,
            total_cost REAL,
            expired TEXT
        );

        CREATE TABLE locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cricos_provider_code TEXT,
            institution_name TEXT,
            location_name TEXT,
            location_type TEXT,
            address TEXT,
            city TEXT,
            state TEXT,
            postcode TEXT
        );

        CREATE TABLE course_locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cricos_provider_code TEXT,
            institution_name TEXT,
            cricos_course_code TEXT,
            location_name TEXT,
            location_city TEXT,
            location_state TEXT
        );
    """)

    print("Inserting institutions...")
    for _, r in df_inst.iterrows():
        addr_parts = [clean_str(r.get(f"Postal Address Line {i}")) for i in range(1, 5)]
        addr = ", ".join(p for p in addr_parts if p)
        c.execute("""INSERT OR REPLACE INTO institutions VALUES (?,?,?,?,?,?,?,?,?,?)""", (
            clean_str(r.get("CRICOS Provider Code")),
            clean_str(r.get("Trading Name")),
            clean_str(r.get("Institution Name")),
            clean_str(r.get("Institution Type")),
            clean_num(r.get("Institution Capacity")),
            clean_str(r.get("Website")),
            addr or None,
            clean_str(r.get("Postal Address City")),
            clean_str(r.get("Postal Address State")),
            clean_str(r.get("Postal Address Postcode")),
        ))

    print("Inserting courses...")
    batch = []
    for _, r in df_courses.iterrows():
        batch.append((
            clean_str(r.get("CRICOS Course Code")),
            clean_str(r.get("CRICOS Provider Code")),
            clean_str(r.get("Institution Name")),
            clean_str(r.get("Course Name")),
            clean_str(r.get("VET National Code")),
            clean_str(r.get("Dual Qualification")),
            clean_str(r.get("Field of Education 1 Broad Field")),
            clean_str(r.get("Field of Education 1 Narrow Field")),
            clean_str(r.get("Field of Education 1 Detailed Field")),
            clean_str(r.get("Course Level")),
            clean_str(r.get("Foundation Studies")),
            clean_str(r.get("Work Component")),
            clean_str(r.get("Course Language")),
            clean_num(r.get("Duration (Weeks)")),
            clean_num(r.get("Tuition Fee")),
            clean_num(r.get("Non Tuition Fee")),
            clean_num(r.get("Estimated Total Course Cost")),
            clean_str(r.get("Expired")),
        ))
    c.executemany("INSERT OR REPLACE INTO courses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", batch)

    print("Inserting locations...")
    for _, r in df_locs.iterrows():
        addr_parts = [clean_str(r.get(f"Address Line {i}")) for i in range(1, 5)]
        addr = ", ".join(p for p in addr_parts if p)
        c.execute("INSERT INTO locations (cricos_provider_code, institution_name, location_name, location_type, address, city, state, postcode) VALUES (?,?,?,?,?,?,?,?)", (
            clean_str(r.get("CRICOS Provider Code")),
            clean_str(r.get("Institution Name")),
            clean_str(r.get("Location Name")),
            clean_str(r.get("Location Type")),
            addr or None,
            clean_str(r.get("City")),
            clean_str(r.get("State")),
            clean_str(r.get("Postcode")),
        ))

    print("Inserting course locations...")
    cl_batch = []
    for _, r in df_cl.iterrows():
        cl_batch.append((
            clean_str(r.get("CRICOS Provider Code")),
            clean_str(r.get("Institution Name")),
            clean_str(r.get("CRICOS Course Code")),
            clean_str(r.get("Location Name")),
            clean_str(r.get("Location City")),
            clean_str(r.get("Location State")),
        ))
    c.executemany("INSERT INTO course_locations (cricos_provider_code, institution_name, cricos_course_code, location_name, location_city, location_state) VALUES (?,?,?,?,?,?)", cl_batch)

    print("Creating search index...")
    c.executescript("""
        CREATE INDEX IF NOT EXISTS idx_courses_provider ON courses(cricos_provider_code);
        CREATE INDEX IF NOT EXISTS idx_courses_level ON courses(course_level);
        CREATE INDEX IF NOT EXISTS idx_courses_field ON courses(field_broad);
        CREATE INDEX IF NOT EXISTS idx_courses_expired ON courses(expired);
        CREATE INDEX IF NOT EXISTS idx_cl_course ON course_locations(cricos_course_code);
        CREATE INDEX IF NOT EXISTS idx_cl_state ON course_locations(location_state);

        CREATE VIRTUAL TABLE IF NOT EXISTS courses_fts USING fts5(
            cricos_course_code UNINDEXED,
            course_name,
            institution_name,
            field_broad,
            field_narrow,
            course_level,
            content=courses,
            content_rowid=rowid
        );

        INSERT INTO courses_fts(courses_fts) VALUES('rebuild');
    """)

    conn.commit()
    conn.close()
    print(f"\nDatabase created: {DB_PATH}")
    print("Setup complete! Run: python app.py")


if __name__ == "__main__":
    main()
