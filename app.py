"""
Australia Courses Finder - Flask Backend
"""
from flask import Flask, render_template, request, jsonify
import sqlite3
import json
import math
import os

app = Flask(__name__)

def _find_db():
    candidates = [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "courses.db"),
        os.path.join(os.getcwd(), "courses.db"),
        "/var/task/courses.db",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]

DB_PATH = _find_db()

SCHOLARSHIPS = [
    {
        "name": "Australia Awards Scholarships",
        "provider": "Australian Government (DFAT)",
        "level": ["Bachelor Degree", "Masters Degree (Coursework)", "Masters Degree (Research)", "Doctoral Degree"],
        "description": "Fully-funded scholarships for students from developing countries to study in Australia. Covers tuition, living allowance, return airfare, health cover, and introductory academic program.",
        "eligibility": "Citizens of eligible countries (Indonesia, India, Pacific nations, and many others). Must not hold Australian citizenship or PR. Age limits may apply by country.",
        "value": "Full tuition + living allowance + airfare + extras",
        "link": "https://www.australiaawards.gov.au/",
        "tags": ["government", "international", "full-funding", "developing countries"]
    },
    {
        "name": "Research Training Program (RTP)",
        "provider": "Australian Government (Department of Education)",
        "level": ["Masters Degree (Research)", "Doctoral Degree"],
        "description": "Provides fee offsets and stipends to domestic and international students undertaking higher degrees by research at Australian universities.",
        "eligibility": "Enrolled in an eligible higher degree by research at an Australian university. Both domestic and international students.",
        "value": "Full tuition fee offset + living stipend (~AUD $33,000/year)",
        "link": "https://www.education.gov.au/research-training-program",
        "tags": ["government", "research", "PhD", "masters", "domestic", "international"]
    },
    {
        "name": "Destination Australia Program",
        "provider": "Australian Government (Department of Education)",
        "level": ["Certificate I", "Certificate II", "Certificate III", "Certificate IV", "Diploma", "Advanced Diploma", "Bachelor Degree", "Masters Degree (Coursework)"],
        "description": "Promotes study and living in regional Australia. Scholarships are available at regional universities, TAFEs, and higher education providers.",
        "eligibility": "Domestic and international students studying at a regional Australian institution.",
        "value": "Up to AUD $15,000 per year",
        "link": "https://www.education.gov.au/destination-australia",
        "tags": ["government", "regional", "domestic", "international", "vocational"]
    },
    {
        "name": "Endeavour Leadership Program (now Australia Awards)",
        "provider": "Australian Government",
        "level": ["Bachelor Degree", "Masters Degree (Coursework)", "Masters Degree (Research)", "Doctoral Degree"],
        "description": "Merit-based scholarships for high achievers from the Indo-Pacific, Middle East, Europe and Americas to undertake study, research or professional development in Australia. Now merged with Australia Awards.",
        "eligibility": "Citizens of eligible countries. Must demonstrate academic excellence and leadership potential.",
        "value": "Full tuition + establishment allowance + travel + monthly stipend",
        "link": "https://www.australiaawards.gov.au/",
        "tags": ["government", "international", "merit", "leadership", "indo-pacific"]
    },
    {
        "name": "Indonesia Australia Partnership — Bima Sakti & LPDP-AAS",
        "provider": "LPDP (Indonesia) + DFAT (Australia)",
        "level": ["Masters Degree (Coursework)", "Masters Degree (Research)", "Doctoral Degree"],
        "description": "Joint scholarship between Indonesia's LPDP and Australia Awards. Supports Indonesian citizens to study at Australian universities at Masters or PhD level.",
        "eligibility": "Indonesian citizens with a bachelor's degree, min. GPA 3.0, working in a relevant field.",
        "value": "Full tuition + living allowance + airfare + insurance",
        "link": "https://www.lpdp.kemenkeu.go.id/",
        "tags": ["indonesia", "government", "bilateral", "masters", "PhD", "international"]
    },
    {
        "name": "University-Specific Scholarships",
        "provider": "Individual Australian Universities",
        "level": ["All levels"],
        "description": "Most Australian universities offer their own merit or need-based scholarships. Examples: Melbourne International Undergraduate Scholarship, Sydney Scholars Awards, ANU Chancellor's International Scholarship, Monash International Leadership Scholarship.",
        "eligibility": "Varies by university and scholarship. Generally based on academic merit. Check each university's website.",
        "value": "Partial to full tuition fee waiver (varies widely)",
        "link": "https://www.studyaustralia.gov.au/english/scholarships",
        "tags": ["university", "merit", "international", "domestic", "partial", "full"]
    },
    {
        "name": "Australian Government International Scholarships — studyaustralia.gov.au",
        "provider": "Australian Government",
        "level": ["All levels"],
        "description": "Central portal listing all Australian government-funded scholarships for international students including Australia Awards, Destination Australia, New Colombo Plan (for Australians studying in the Indo-Pacific), and more.",
        "eligibility": "Varies per scholarship. Most are for international students from specific regions.",
        "value": "Varies — from partial to full funding",
        "link": "https://www.studyaustralia.gov.au/english/scholarships",
        "tags": ["government", "international", "portal", "all levels"]
    },
    {
        "name": "State & Territory Government Scholarships",
        "provider": "State Governments (NSW, VIC, QLD, WA, SA, etc.)",
        "level": ["All levels"],
        "description": "Individual Australian states offer scholarships to attract international students. E.g. NSW: NSW International Student Scholarships; VIC: Study Melbourne Scholarships; WA: Western Australian International Scholarship.",
        "eligibility": "Varies by state. International students enrolled at a university/TAFE in that state.",
        "value": "Partial tuition or living stipend",
        "link": "https://www.studyaustralia.gov.au/english/scholarships",
        "tags": ["state", "government", "international", "regional"]
    },
    {
        "name": "Commonwealth Scientific and Industrial Research Organisation (CSIRO) Postgraduate Scholarships",
        "provider": "CSIRO",
        "level": ["Masters Degree (Research)", "Doctoral Degree"],
        "description": "Research scholarships for students working on CSIRO-related research projects in science, engineering, environment, and technology fields.",
        "eligibility": "Australian and New Zealand citizens or permanent residents enrolled in an Australian university.",
        "value": "Stipend ~AUD $35,000/year + top-up possible",
        "link": "https://www.csiro.au/en/careers/scholarships",
        "tags": ["research", "STEM", "domestic", "PhD", "masters"]
    },
    {
        "name": "The Rotary Foundation Scholarships",
        "provider": "Rotary International",
        "level": ["Bachelor Degree", "Masters Degree (Coursework)", "Doctoral Degree"],
        "description": "Global Grant Scholarships support university-level academic studies or vocational training that aligns with Rotary's areas of focus (peace, disease prevention, water, education, economic development, environment).",
        "eligibility": "Must have Rotary club sponsorship. Open to all nationalities. Study in a country other than your home country.",
        "value": "Minimum USD $30,000",
        "link": "https://www.rotary.org/en/our-programs/scholarships",
        "tags": ["international", "rotary", "NGO", "community", "all nationalities"]
    }
]


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def format_currency(val):
    if val is None:
        return "N/A"
    return f"AUD ${val:,.0f}"


def format_duration(weeks):
    if weeks is None:
        return "N/A"
    weeks = int(weeks)
    if weeks < 52:
        return f"{weeks} weeks"
    years = weeks / 52
    if years == int(years):
        return f"{int(years)} year{'s' if years > 1 else ''}"
    return f"{years:.1f} years ({weeks} weeks)"


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def search():
    q = request.args.get("q", "").strip()
    course_level = request.args.get("level", "")
    field = request.args.get("field", "")
    state = request.args.get("state", "")
    min_fee = request.args.get("min_fee", "")
    max_fee = request.args.get("max_fee", "")
    duration_range = request.args.get("duration", "")
    expired = request.args.get("expired", "No")
    page = int(request.args.get("page", 1))
    per_page = 20

    conn = get_db()
    c = conn.cursor()

    conditions = []
    params = []

    if expired:
        conditions.append("c.expired = ?")
        params.append(expired)

    if course_level:
        conditions.append("c.course_level = ?")
        params.append(course_level)

    if field:
        conditions.append("c.field_broad = ?")
        params.append(field)

    if min_fee:
        conditions.append("c.total_cost >= ?")
        params.append(float(min_fee))

    if max_fee:
        conditions.append("c.total_cost <= ?")
        params.append(float(max_fee))

    if duration_range and "," in duration_range:
        dur_parts = duration_range.split(",")
        try:
            min_dur = float(dur_parts[0])
            max_dur = float(dur_parts[1])
            conditions.append("c.duration_weeks >= ?")
            params.append(min_dur)
            if max_dur < 999:
                conditions.append("c.duration_weeks < ?")
                params.append(max_dur)
        except (ValueError, IndexError):
            pass

    if state:
        # Join with course_locations for state filter
        state_subquery = """c.cricos_course_code IN (
            SELECT DISTINCT cricos_course_code FROM course_locations WHERE location_state = ?
        )"""
        conditions.append(state_subquery)
        params.append(state)

    where_base = " AND ".join(conditions) if conditions else "1=1"

    if q:
        fts_query = " OR ".join(f'"{word}"' if " " in word else word + "*" for word in q.split())
        fts_query = q.replace('"', '""') + "*"

        sql_count = f"""
            SELECT COUNT(*) FROM courses c
            JOIN courses_fts ON courses_fts.cricos_course_code = c.cricos_course_code
            WHERE courses_fts MATCH ? AND {where_base}
        """
        sql_data = f"""
            SELECT c.*, rank FROM courses c
            JOIN courses_fts ON courses_fts.cricos_course_code = c.cricos_course_code
            WHERE courses_fts MATCH ? AND {where_base}
            ORDER BY rank
            LIMIT ? OFFSET ?
        """
        count_params = [fts_query] + params
        data_params = [fts_query] + params + [per_page, (page - 1) * per_page]
    else:
        sql_count = f"SELECT COUNT(*) FROM courses c WHERE {where_base}"
        sql_data = f"""
            SELECT c.* FROM courses c WHERE {where_base}
            ORDER BY c.institution_name, c.course_name
            LIMIT ? OFFSET ?
        """
        count_params = params
        data_params = params + [per_page, (page - 1) * per_page]

    try:
        total = c.execute(sql_count, count_params).fetchone()[0]
        rows = c.execute(sql_data, data_params).fetchall()
    except sqlite3.OperationalError:
        # FTS fallback to LIKE search
        like_q = f"%{q}%"
        like_cond = f"(c.course_name LIKE ? OR c.institution_name LIKE ? OR c.field_broad LIKE ?)"
        full_where = f"{like_cond} AND {where_base}" if where_base != "1=1" else like_cond
        like_params = [like_q, like_q, like_q] + params
        total = c.execute(f"SELECT COUNT(*) FROM courses c WHERE {full_where}", like_params).fetchone()[0]
        rows = c.execute(f"SELECT c.* FROM courses c WHERE {full_where} ORDER BY c.course_name LIMIT ? OFFSET ?",
                         like_params + [per_page, (page - 1) * per_page]).fetchall()

    results = []
    for r in rows:
        d = dict(r)
        # Get states for this course
        states = c.execute(
            "SELECT DISTINCT location_state FROM course_locations WHERE cricos_course_code = ?",
            (d["cricos_course_code"],)
        ).fetchall()
        d["states"] = sorted([s[0] for s in states if s[0]])
        d["duration_formatted"] = format_duration(d.get("duration_weeks"))
        d["fee_formatted"] = format_currency(d.get("total_cost"))
        d["tuition_formatted"] = format_currency(d.get("tuition_fee"))
        results.append(d)

    conn.close()

    return jsonify({
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": math.ceil(total / per_page),
        "results": results
    })


@app.route("/api/course/<code>")
def course_detail(code):
    conn = get_db()
    c = conn.cursor()

    course = c.execute("SELECT * FROM courses WHERE cricos_course_code = ?", (code,)).fetchone()
    if not course:
        conn.close()
        return jsonify({"error": "Not found"}), 404

    d = dict(course)

    locations = c.execute("""
        SELECT cl.location_name, cl.location_city, cl.location_state,
               l.address, l.location_type
        FROM course_locations cl
        LEFT JOIN locations l ON cl.cricos_provider_code = l.cricos_provider_code
            AND cl.location_name = l.location_name
        WHERE cl.cricos_course_code = ?
        ORDER BY cl.location_state, cl.location_city
    """, (code,)).fetchall()

    institution = c.execute("SELECT * FROM institutions WHERE cricos_provider_code = ?",
                            (d["cricos_provider_code"],)).fetchone()

    d["locations"] = [dict(l) for l in locations]
    d["institution"] = dict(institution) if institution else {}
    d["duration_formatted"] = format_duration(d.get("duration_weeks"))
    d["fee_formatted"] = format_currency(d.get("total_cost"))
    d["tuition_formatted"] = format_currency(d.get("tuition_fee"))
    d["non_tuition_formatted"] = format_currency(d.get("non_tuition_fee"))

    conn.close()
    return jsonify(d)


LEVEL_ORDER = {
    "Certificate I": 1, "Certificate II": 2, "Certificate III": 3,
    "Certificate IV": 4, "Diploma": 5, "Advanced Diploma": 6,
    "Associate Degree": 7, "Bachelor Degree": 8, "Bachelor Honours Degree": 9,
}
VET_LEVELS = set(k for k, v in LEVEL_ORDER.items() if v <= 6)
BACHELOR_LEVELS = {"Bachelor Degree", "Bachelor Honours Degree", "Associate Degree"}
DIPLOMA_LEVELS = {"Diploma", "Advanced Diploma"}
PACKAGE_BASE_LEVELS = VET_LEVELS  # base course must be VET


def _fmt_course(r):
    return {
        "cricos_course_code": r.get("cricos_course_code"),
        "course_name": r.get("course_name"),
        "course_level": r.get("course_level"),
        "duration_weeks": r.get("duration_weeks"),
        "duration_formatted": format_duration(r.get("duration_weeks")),
        "fee_formatted": format_currency(r.get("total_cost")),
        "total_cost": r.get("total_cost") or 0,
    }


@app.route("/api/packages/<code>")
def course_packages(code):
    conn = get_db()
    c = conn.cursor()

    row = c.execute("SELECT * FROM courses WHERE cricos_course_code = ?", (code,)).fetchone()
    if not row:
        conn.close()
        return jsonify([])

    base = dict(row)
    base_level = base.get("course_level")
    base_order = LEVEL_ORDER.get(base_level, 0)

    if base_level not in PACKAGE_BASE_LEVELS:
        conn.close()
        return jsonify([])

    base_dur = float(base.get("duration_weeks") or 0)
    provider = base["cricos_provider_code"]
    field_narrow = base.get("field_narrow")
    field_broad = base.get("field_broad")

    # Eligible companion levels: strictly higher than base
    # If base is Diploma/Advanced Diploma, also include Bachelor levels
    eligible = [l for l, o in LEVEL_ORDER.items() if o > base_order]
    if base_level not in DIPLOMA_LEVELS:
        eligible = [l for l in eligible if l not in BACHELOR_LEVELS]

    if not eligible:
        conn.close()
        return jsonify([])

    ph = ",".join("?" * len(eligible))

    def fetch_candidates(field_col, field_val):
        if not field_val:
            return []
        rows = c.execute(f"""
            SELECT * FROM courses
            WHERE cricos_provider_code = ?
              AND cricos_course_code != ?
              AND course_level IN ({ph})
              AND expired = 'No'
              AND duration_weeks IS NOT NULL
              AND duration_weeks > 0
              AND {field_col} = ?
        """, [provider, code] + eligible + [field_val]).fetchall()
        return [dict(r) for r in rows]

    candidates = fetch_candidates("field_narrow", field_narrow)
    if not candidates:
        candidates = fetch_candidates("field_broad", field_broad)

    # Sort candidates by level order ascending
    candidates.sort(key=lambda r: LEVEL_ORDER.get(r.get("course_level"), 99))

    # Group by level order for chain building
    from collections import defaultdict
    by_order = defaultdict(list)
    for cand in candidates:
        o = LEVEL_ORDER.get(cand.get("course_level"), 99)
        by_order[o].append(cand)

    sorted_orders = sorted(by_order.keys())

    def effective_dur(course_dict, prev_level=None):
        dur = float(course_dict.get("duration_weeks") or 0)
        # 1-year credit if preceded by a diploma into a bachelor
        if prev_level in DIPLOMA_LEVELS and course_dict.get("course_level") in BACHELOR_LEVELS:
            dur = max(0, dur - 52)
        return dur

    packages = []
    seen = set()

    # ── PAIRS: base + 1 companion ──
    for o1 in sorted_orders:
        for c1 in by_order[o1]:
            dur1 = effective_dur(c1, base_level)
            total = base_dur + dur1
            if total < 104:
                continue
            key = (code, c1["cricos_course_code"])
            if key in seen:
                continue
            seen.add(key)
            credit = base_level in DIPLOMA_LEVELS and c1.get("course_level") in BACHELOR_LEVELS
            packages.append({
                "chain": [_fmt_course(base), _fmt_course(c1)],
                "diploma_credit": credit,
                "total_weeks": total,
                "total_formatted": format_duration(total),
                "total_cost": base.get("total_cost", 0) + c1.get("total_cost", 0),
            })

    # ── TRIPLES: base + 2 companions (ascending levels) ──
    for i, o1 in enumerate(sorted_orders):
        for o2 in sorted_orders:
            if o2 <= o1:
                continue
            for c1 in by_order[o1]:
                for c2 in by_order[o2]:
                    if c1["cricos_course_code"] == c2["cricos_course_code"]:
                        continue
                    dur1 = effective_dur(c1, base_level)
                    dur2 = effective_dur(c2, c1.get("course_level"))
                    total = base_dur + dur1 + dur2
                    if total < 104:
                        continue
                    key = tuple(sorted([code, c1["cricos_course_code"], c2["cricos_course_code"]]))
                    if key in seen:
                        continue
                    seen.add(key)
                    credit = (base_level in DIPLOMA_LEVELS and c1.get("course_level") in BACHELOR_LEVELS) or \
                             (c1.get("course_level") in DIPLOMA_LEVELS and c2.get("course_level") in BACHELOR_LEVELS)
                    packages.append({
                        "chain": [_fmt_course(base), _fmt_course(c1), _fmt_course(c2)],
                        "diploma_credit": credit,
                        "total_weeks": total,
                        "total_formatted": format_duration(total),
                        "total_cost": (base.get("total_cost") or 0) + (c1.get("total_cost") or 0) + (c2.get("total_cost") or 0),
                    })

    # Prefer shorter chains, then closest to 2 years
    packages.sort(key=lambda p: (len(p["chain"]), p["total_weeks"]))
    conn.close()
    return jsonify(packages[:8])


@app.route("/api/filters")
def get_filters():
    conn = get_db()
    c = conn.cursor()

    levels = [r[0] for r in c.execute(
        "SELECT DISTINCT course_level FROM courses WHERE course_level IS NOT NULL ORDER BY course_level"
    ).fetchall()]

    fields = [r[0] for r in c.execute(
        "SELECT DISTINCT field_broad FROM courses WHERE field_broad IS NOT NULL ORDER BY field_broad"
    ).fetchall()]

    states = [r[0] for r in c.execute(
        "SELECT DISTINCT location_state FROM course_locations WHERE location_state IS NOT NULL ORDER BY location_state"
    ).fetchall()]

    conn.close()
    return jsonify({"levels": levels, "fields": fields, "states": states})


@app.route("/api/scholarships")
def get_scholarships():
    q = request.args.get("q", "").lower()
    level = request.args.get("level", "")

    results = []
    for s in SCHOLARSHIPS:
        if q and q not in s["name"].lower() and q not in s["description"].lower() and \
           not any(q in t for t in s["tags"]):
            continue
        if level and level not in s["level"] and "All levels" not in s["level"]:
            continue
        results.append(s)

    return jsonify(results)


@app.route("/api/stats")
def stats():
    conn = get_db()
    c = conn.cursor()
    total_courses = c.execute("SELECT COUNT(*) FROM courses WHERE expired='No'").fetchone()[0]
    total_inst = c.execute("SELECT COUNT(*) FROM institutions").fetchone()[0]
    total_states = c.execute("SELECT COUNT(DISTINCT location_state) FROM course_locations").fetchone()[0]
    conn.close()
    return jsonify({
        "courses": total_courses,
        "institutions": total_inst,
        "states": total_states,
        "scholarships": len(SCHOLARSHIPS)
    })


if __name__ == "__main__":
    import os
    if not os.path.exists(DB_PATH):
        print("Database not found. Please run: python setup_db.py")
    else:
        print("Starting Australia Courses Finder...")
        print("Open: http://localhost:5000")
        app.run(debug=True, port=5000)
