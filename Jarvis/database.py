"""
database.py — JARVIS V1 Data Layer
-----------------------------------
Handles all SQLite database operations.
This file defines the schema (tables) and provides helper functions
so that app.py never has to write raw SQL — it just calls these functions.

The database file (data/jarvis.db) is created automatically on first run.
"""

import sqlite3
import os
from datetime import datetime, date

# Path to the SQLite database file
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "jarvis.db")


def get_connection():
    """Open and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Allows accessing columns by name (row["column"])
    return conn


def initialize_database():
    """
    Create all tables if they don't already exist.
    Safe to call on every startup — it won't delete existing data.
    """
    conn = get_connection()
    c = conn.cursor()

    # --- Mission Config Table ---
    # Stores the single mission start date and your name.
    c.execute("""
        CREATE TABLE IF NOT EXISTS mission_config (
            id          INTEGER PRIMARY KEY,
            start_date  TEXT NOT NULL,
            your_name   TEXT DEFAULT 'Agent'
        )
    """)

    # --- Daily Log Table ---
    # One row per day. Tracks your daily execution consistency.
    c.execute("""
        CREATE TABLE IF NOT EXISTS daily_log (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            log_date        TEXT NOT NULL UNIQUE,
            focus_hours     REAL DEFAULT 0,
            apps_submitted  INTEGER DEFAULT 0,
            labs_completed  INTEGER DEFAULT 0,
            notes           TEXT DEFAULT ''
        )
    """)

    # --- Job Applications Table ---
    # Every job application you submit goes here.
    c.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            company         TEXT NOT NULL,
            role_title      TEXT NOT NULL,
            role_category   TEXT NOT NULL,
            job_url         TEXT DEFAULT '',
            applied_date    TEXT NOT NULL,
            status          TEXT DEFAULT 'Applied',
            follow_up_date  TEXT DEFAULT '',
            salary_range    TEXT DEFAULT '',
            notes           TEXT DEFAULT '',
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Skills Checklist Table ---
    # Tracks your technical skill milestones.
    c.execute("""
        CREATE TABLE IF NOT EXISTS skill_milestones (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            category    TEXT NOT NULL,
            milestone   TEXT NOT NULL,
            done        INTEGER DEFAULT 0,
            notes       TEXT DEFAULT ''
        )
    """)

    # --- Daily Planner Tasks Table ---
    # Stores the task template for each mission day (day_number 1-50).
    # Each row is one task block for one day.
    c.execute("""
        CREATE TABLE IF NOT EXISTS planner_tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            day_number  INTEGER NOT NULL,
            time_block  TEXT NOT NULL,
            task_title  TEXT NOT NULL,
            task_detail TEXT DEFAULT '',
            category    TEXT DEFAULT 'General',
            sort_order  INTEGER DEFAULT 0
        )
    """)

    # --- Planner Completions Table ---
    # Tracks which tasks were actually completed on which calendar date.
    # Separated from planner_tasks so editing a task doesn't wipe completion history.
    c.execute("""
        CREATE TABLE IF NOT EXISTS planner_completions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id     INTEGER NOT NULL,
            done_date   TEXT NOT NULL,
            done        INTEGER DEFAULT 0,
            UNIQUE(task_id, done_date)
        )
    """)

    # --- Learning Resources Table ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS learning_resources (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            topic           TEXT NOT NULL,
            skill_category  TEXT NOT NULL,
            resource_title  TEXT NOT NULL,
            provider        TEXT NOT NULL,
            url             TEXT DEFAULT '',
            access_note     TEXT DEFAULT 'Free',
            learning_obj    TEXT DEFAULT '',
            sequence_num    INTEGER DEFAULT 0,
            est_hours       REAL DEFAULT 1.0,
            practical_ex    TEXT DEFAULT '',
            expected_output TEXT DEFAULT '',
            done            INTEGER DEFAULT 0,
            personal_notes  TEXT DEFAULT '',
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Portfolio Items Table ---
    c.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            title           TEXT NOT NULL,
            category        TEXT NOT NULL,
            description     TEXT DEFAULT '',
            evidence_url    TEXT DEFAULT '',
            skills_shown    TEXT DEFAULT '',
            status          TEXT DEFAULT 'In Progress',
            date_completed  TEXT DEFAULT '',
            personal_notes  TEXT DEFAULT '',
            created_at      TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # --- Mission Days Table (50-Day Mission Cards) ---
    # Stores the complete 19-field mission card for each day (1-50).
    c.execute("""
        CREATE TABLE IF NOT EXISTS mission_days (
            day_number              INTEGER PRIMARY KEY,
            phase                   TEXT NOT NULL,
            mission_title           TEXT NOT NULL,
            career_relevance        TEXT DEFAULT '',
            learning_target         TEXT DEFAULT '',
            step_by_step_method     TEXT DEFAULT '',
            time_allocation         TEXT DEFAULT '60m Learning · 90m Practical · 45m Portfolio/Deliverable · 45m Interview/Review (4h)',
            resources_text          TEXT DEFAULT '',
            required_tools          TEXT DEFAULT '',
            deliverable             TEXT DEFAULT '',
            completion_criteria     TEXT DEFAULT '',
            checkpoint_questions    TEXT DEFAULT '',
            common_mistakes         TEXT DEFAULT '',
            interview_question      TEXT DEFAULT '',
            resume_relevance        TEXT DEFAULT '',
            status                  TEXT DEFAULT 'Not Started',
            personal_notes          TEXT DEFAULT '',
            blocker_next_action     TEXT DEFAULT ''
        )
    """)

    # --- Safe Migrations for Existing Tables ---
    # Add new columns to planner_tasks without dropping existing rows
    pt_cols = {r[1] for r in c.execute("PRAGMA table_info(planner_tasks)").fetchall()}
    if "est_minutes" not in pt_cols:
        c.execute("ALTER TABLE planner_tasks ADD COLUMN est_minutes INTEGER DEFAULT 45")
    if "resource_url" not in pt_cols:
        c.execute("ALTER TABLE planner_tasks ADD COLUMN resource_url TEXT DEFAULT ''")
    if "expected_output" not in pt_cols:
        c.execute("ALTER TABLE planner_tasks ADD COLUMN expected_output TEXT DEFAULT ''")

    # Add new columns to applications without dropping existing rows
    app_cols = {r[1] for r in c.execute("PRAGMA table_info(applications)").fetchall()}
    if "location" not in app_cols:
        c.execute("ALTER TABLE applications ADD COLUMN location TEXT DEFAULT ''")
    if "resume_version" not in app_cols:
        c.execute("ALTER TABLE applications ADD COLUMN resume_version TEXT DEFAULT ''")
    if "keywords" not in app_cols:
        c.execute("ALTER TABLE applications ADD COLUMN keywords TEXT DEFAULT ''")

    # Add new columns to learning_resources for strict free-only policy
    lr_cols = {r[1] for r in c.execute("PRAGMA table_info(learning_resources)").fetchall()}
    if "exact_free_content" not in lr_cols:
        c.execute("ALTER TABLE learning_resources ADD COLUMN exact_free_content TEXT DEFAULT ''")
    if "relevant_days" not in lr_cols:
        c.execute("ALTER TABLE learning_resources ADD COLUMN relevant_days TEXT DEFAULT ''")
    if "registration_required" not in lr_cols:
        c.execute("ALTER TABLE learning_resources ADD COLUMN registration_required TEXT DEFAULT 'No'")
    if "free_alternative" not in lr_cols:
        c.execute("ALTER TABLE learning_resources ADD COLUMN free_alternative TEXT DEFAULT ''")
    if "last_verified" not in lr_cols:
        c.execute("ALTER TABLE learning_resources ADD COLUMN last_verified TEXT DEFAULT '2026-11-25'")

    conn.commit()
    conn.close()
    _seed_default_milestones()
    _seed_planner_tasks()
    _seed_learning_resources()
    _seed_50day_mission_roadmap()


def _seed_default_milestones():
    """
    Insert a default set of skill milestones only if the table is empty.
    These represent a balanced technical job seeker roadmap.
    """
    conn = get_connection()
    c = conn.cursor()
    count = c.execute("SELECT COUNT(*) FROM skill_milestones").fetchone()[0]
    if count == 0:
        defaults = [
            # Foundational
            ("Foundations", "Networking fundamentals (OSI, TCP/IP, DNS, DHCP)"),
            ("Foundations", "Linux command line basics (navigation, permissions, processes)"),
            ("Foundations", "Windows administration basics (AD, Group Policy, Event Logs)"),
            # Cybersecurity / SOC
            ("Cybersecurity", "Set up a home lab (VirtualBox or VMware)"),
            ("Cybersecurity", "Complete a TryHackMe / HackTheBox beginner path"),
            ("Cybersecurity", "Understand SIEM basics (Splunk or Elastic free tier)"),
            ("Cybersecurity", "Study CompTIA Security+ syllabus (or CEH)"),
            ("Cybersecurity", "Complete one VAPT lab (Nmap, Metasploit, Burp Suite)"),
            # IT / Technical Support
            ("IT Support", "Understand ITIL ticketing workflow (incidents, change, problem)"),
            ("IT Support", "Practice remote desktop support tools (RDP, AnyDesk)"),
            ("IT Support", "Learn basic scripting for support automation (PowerShell/Bash)"),
            # Application Support / NOC
            ("App Support / NOC", "Understand application monitoring concepts (uptime, latency, alerts)"),
            ("App Support / NOC", "Learn log analysis and basic SQL queries for troubleshooting"),
            ("App Support / NOC", "Study on-call escalation and incident runbook practices"),
            # Job Search Execution
            ("Job Search", "Polish resume for each role category"),
            ("Job Search", "Create / update LinkedIn profile with relevant keywords"),
            ("Job Search", "Draft 3 tailored cover letter templates"),
            ("Job Search", "Reach out to 10 recruiters on LinkedIn"),
            ("Job Search", "Complete 5 mock technical interviews (use Pramp or peers)"),
        ]
        c.executemany(
            "INSERT INTO skill_milestones (category, milestone) VALUES (?, ?)",
            defaults
        )
        conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# MISSION CONFIG
# ─────────────────────────────────────────────────────────────────────────────

def get_mission_config():
    conn = get_connection()
    row = conn.execute("SELECT * FROM mission_config WHERE id = 1").fetchone()
    conn.close()
    return dict(row) if row else None


def set_mission_config(start_date: str, your_name: str):
    conn = get_connection()
    conn.execute("DELETE FROM mission_config")
    conn.execute(
        "INSERT INTO mission_config (id, start_date, your_name) VALUES (1, ?, ?)",
        (start_date, your_name)
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# DAILY LOG
# ─────────────────────────────────────────────────────────────────────────────

def upsert_daily_log(log_date: str, focus_hours: float, apps_submitted: int, labs_completed: int, notes: str):
    """Insert today's log, or update it if it already exists."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO daily_log (log_date, focus_hours, apps_submitted, labs_completed, notes)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(log_date) DO UPDATE SET
            focus_hours     = excluded.focus_hours,
            apps_submitted  = excluded.apps_submitted,
            labs_completed  = excluded.labs_completed,
            notes           = excluded.notes
    """, (log_date, focus_hours, apps_submitted, labs_completed, notes))
    conn.commit()
    conn.close()


def get_all_daily_logs():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM daily_log ORDER BY log_date DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_today_log(today: str):
    conn = get_connection()
    row = conn.execute("SELECT * FROM daily_log WHERE log_date = ?", (today,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_streak():
    """
    Count the number of consecutive days (ending today or yesterday)
    where a daily log entry exists.
    """
    conn = get_connection()
    rows = conn.execute("SELECT log_date FROM daily_log ORDER BY log_date DESC").fetchall()
    conn.close()
    if not rows:
        return 0
    dates = sorted([r["log_date"] for r in rows], reverse=True)
    today_str = date.today().isoformat()
    streak = 0
    check_date = date.today()
    for d in dates:
        if d == check_date.isoformat():
            streak += 1
            check_date = date.fromordinal(check_date.toordinal() - 1)
        else:
            break
    return streak


# ─────────────────────────────────────────────────────────────────────────────
# APPLICATIONS
# ─────────────────────────────────────────────────────────────────────────────

ROLE_CATEGORIES = [
    "SOC Analyst / Cybersecurity",
    "VAPT / Security Testing",
    "IT Support / Technical Support",
    "Application Support / NOC",
    "Other Technical Roles",
]

APPLICATION_STATUSES = [
    "Applied",
    "Recruiter Response",
    "Interview Scheduled",
    "Interview Done",
    "Follow-Up Sent",
    "Offer Received",
    "Rejected",
    "Withdrawn",
]


def add_application(company, role_title, role_category, job_url, applied_date,
                    status, follow_up_date, salary_range, notes,
                    location="", resume_version="", keywords=""):
    conn = get_connection()
    conn.execute("""
        INSERT INTO applications
            (company, role_title, role_category, job_url, applied_date,
             status, follow_up_date, salary_range, notes,
             location, resume_version, keywords)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (company, role_title, role_category, job_url, applied_date,
          status, follow_up_date, salary_range, notes,
          location, resume_version, keywords))
    conn.commit()
    conn.close()


def get_all_applications(status_filter=None, category_filter=None):
    conn = get_connection()
    query = "SELECT * FROM applications WHERE 1=1"
    params = []
    if status_filter and status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    if category_filter and category_filter != "All":
        query += " AND role_category = ?"
        params.append(category_filter)
    query += " ORDER BY applied_date DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def update_application_status(app_id: int, new_status: str, follow_up_date: str = "", notes: str = ""):
    conn = get_connection()
    conn.execute("""
        UPDATE applications
        SET status = ?, follow_up_date = ?, notes = ?
        WHERE id = ?
    """, (new_status, follow_up_date, notes, app_id))
    conn.commit()
    conn.close()


def delete_application(app_id: int):
    conn = get_connection()
    conn.execute("DELETE FROM applications WHERE id = ?", (app_id,))
    conn.commit()
    conn.close()


def get_application_summary():
    """Return a dict of status counts for the dashboard metrics."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT status, COUNT(*) as cnt FROM applications GROUP BY status"
    ).fetchall()
    conn.close()
    summary = {r["status"]: r["cnt"] for r in rows}
    return summary


def get_follow_ups_due(today: str):
    """Return applications where a follow-up is due today or overdue."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT * FROM applications
        WHERE follow_up_date != '' AND follow_up_date <= ?
        AND status NOT IN ('Offer Received', 'Rejected', 'Withdrawn')
        ORDER BY follow_up_date ASC
    """, (today,)).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ─────────────────────────────────────────────────────────────────────────────
# SKILL MILESTONES
# ─────────────────────────────────────────────────────────────────────────────

def get_all_milestones():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM skill_milestones ORDER BY category, id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def toggle_milestone(milestone_id: int, done: bool):
    conn = get_connection()
    conn.execute("UPDATE skill_milestones SET done = ? WHERE id = ?", (1 if done else 0, milestone_id))
    conn.commit()
    conn.close()


def add_milestone(category: str, milestone: str):
    conn = get_connection()
    conn.execute("INSERT INTO skill_milestones (category, milestone) VALUES (?, ?)", (category, milestone))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# EXPORT / BACKUP
# ─────────────────────────────────────────────────────────────────────────────

def export_to_csv(table_name: str) -> str:
    """
    Export a table to a CSV string and return it.
    Used by the Streamlit download button.
    """
    import csv
    import io
    conn = get_connection()
    rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
    conn.close()
    if not rows:
        return ""
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows([dict(r) for r in rows])
    return output.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# DAILY PLANNER — TASK TEMPLATES
# ─────────────────────────────────────────────────────────────────────────────

# Time block labels used consistently across the planner
TIME_BLOCKS = [
    "Morning  07:00–09:00",
    "Block 1  09:00–11:00",
    "Block 2  11:00–13:00",
    "Break    13:00–14:00",
    "Block 3  14:00–16:00",
    "Evening  18:00–20:00",
]

TASK_CATEGORIES = [
    "Learning",
    "Lab / Practical",
    "Job Search",
    "Interview Prep",
    "Portfolio",
    "Admin / Setup",
    "Review",
    "General",
]


def _seed_planner_tasks():
    """
    Seed the 50-day mission plan only if the table is empty.
    Days 1-9: Preparation phase. Day 10+: Active job search phase.
    Each day has up to 4 focused work blocks (~4 hours total work).
    """
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM planner_tasks").fetchone()[0]
    if count > 0:
        conn.close()
        return

    # Format: (day, time_block_label, title, detail, category, sort_order)
    tasks = [
        # ── DAY 1 ── Mission Setup & Environment
        (1, "Morning  07:00–09:00",  "Mission briefing & goal setting",
         "Write down your 50-day goal. Define target roles, salary expectations, and your top 3 skills to build.", "Admin / Setup", 1),
        (1, "Block 1  09:00–11:00",  "Set up your tools & workspace",
         "Install VirtualBox, VS Code, Python, and Obsidian (or Notion). Organise your JARVIS folders.", "Admin / Setup", 2),
        (1, "Block 2  11:00–13:00",  "Networking fundamentals — OSI & TCP/IP",
         "Study OSI model layers and TCP/IP stack. Use Professor Messer or free YouTube resources.", "Learning", 3),
        (1, "Block 3  14:00–16:00",  "Linux basics — navigation & file system",
         "Practice cd, ls, pwd, mkdir, cp, mv, rm, cat, grep in a terminal. Use TryHackMe Linux Fundamentals Room 1.", "Lab / Practical", 4),
        (1, "Evening  18:00–20:00",  "Day 1 review & JARVIS log entry",
         "Complete your JARVIS daily check-in. Write 3 things learned. Plan tomorrow.", "Review", 5),

        # ── DAY 2 ── Linux & Networking Depth
        (2, "Morning  07:00–09:00",  "Linux — users, permissions & processes",
         "Study chmod, chown, sudo, ps, top, kill. TryHackMe Linux Fundamentals Room 2.", "Learning", 1),
        (2, "Block 1  09:00–11:00",  "Networking — DNS, DHCP, HTTP/S, ports",
         "Understand common ports (22, 80, 443, 3389). Practice with Wireshark basics.", "Learning", 2),
        (2, "Block 2  11:00–13:00",  "Set up Kali Linux VM",
         "Install Kali Linux in VirtualBox. Verify tools: nmap, netcat, wireshark are available.", "Admin / Setup", 3),
        (2, "Block 3  14:00–16:00",  "TryHackMe — Pre-Security path",
         "Start the TryHackMe Pre-Security learning path (free). Complete at least 2 rooms.", "Lab / Practical", 4),
        (2, "Evening  18:00–20:00",  "Review & JARVIS check-in",
         "Log focus hours and completed labs. Note any concepts that need revisiting.", "Review", 5),

        # ── DAY 3 ── Windows & Active Directory Basics
        (3, "Morning  07:00–09:00",  "Windows administration basics",
         "Study Windows Event Logs (Event Viewer), Task Manager, Services, and Registry basics.", "Learning", 1),
        (3, "Block 1  09:00–11:00",  "Active Directory concepts",
         "Understand Domain Controllers, Users, Groups, OUs, GPOs. Watch a free AD fundamentals video.", "Learning", 2),
        (3, "Block 2  11:00–13:00",  "TryHackMe — Active Directory Basics room",
         "Complete TryHackMe 'Active Directory Basics' room (free).", "Lab / Practical", 3),
        (3, "Block 3  14:00–16:00",  "PowerShell scripting basics",
         "Practice Get-Process, Get-Service, Get-EventLog, Write-Output in PowerShell.", "Lab / Practical", 4),
        (3, "Evening  18:00–20:00",  "Review & JARVIS check-in",
         "Update Skills Tracker in JARVIS. Mark completed milestones.", "Review", 5),

        # ── DAY 4 ── SOC & SIEM Introduction
        (4, "Morning  07:00–09:00",  "SOC roles & responsibilities",
         "Research SOC Tier 1/2/3 analyst roles. Read a few job descriptions for SOC Analyst positions.", "Learning", 1),
        (4, "Block 1  09:00–11:00",  "SIEM fundamentals — what it is and why it matters",
         "Study what a SIEM does (log aggregation, correlation, alerting). Compare Splunk, QRadar, Elastic SIEM.", "Learning", 2),
        (4, "Block 2  11:00–13:00",  "Splunk free training — Splunk Fundamentals 1",
         "Register at Splunk Free Training. Begin 'Splunk Fundamentals 1' (free self-paced course).", "Lab / Practical", 3),
        (4, "Block 3  14:00–16:00",  "TryHackMe — Splunk room or SOC Level 1 path",
         "Start TryHackMe SOC Level 1 learning path. Complete the first room.", "Lab / Practical", 4),
        (4, "Evening  18:00–20:00",  "Review & JARVIS check-in",
         "What is a SIEM alert? Could you explain it in an interview? Write a brief answer.", "Review", 5),

        # ── DAY 5 ── Threat Intelligence & Security Concepts
        (5, "Morning  07:00–09:00",  "Cyber threat landscape overview",
         "Study common attack types: phishing, ransomware, MITM, SQL injection, privilege escalation.", "Learning", 1),
        (5, "Block 1  09:00–11:00",  "MITRE ATT&CK framework",
         "Explore attack.mitre.org. Understand Tactics, Techniques, and Procedures (TTPs).", "Learning", 2),
        (5, "Block 2  11:00–13:00",  "TryHackMe — Cyber Defence path rooms",
         "Complete TryHackMe rooms on Threat Intelligence and MITRE ATT&CK.", "Lab / Practical", 3),
        (5, "Block 3  14:00–16:00",  "Nmap basics — network scanning",
         "Practice nmap -sV, -sC, -O, -p on your local Kali VM lab environment.", "Lab / Practical", 4),
        (5, "Evening  18:00–20:00",  "Review & JARVIS check-in",
         "List 5 attack techniques you now understand. Update skills tracker.", "Review", 5),

        # ── DAY 6 ── Resume Foundation
        (6, "Morning  07:00–09:00",  "Research target job descriptions",
         "Find 10 live job postings for SOC Analyst, IT Support, App Support. Copy key requirements.", "Job Search", 1),
        (6, "Block 1  09:00–11:00",  "Draft your base resume",
         "Write a clean 1-page resume. Include: summary, skills, experience/projects, education, certifications.", "Portfolio", 2),
        (6, "Block 2  11:00–13:00",  "Resume keyword optimisation",
         "Compare your resume to job descriptions. Add missing keywords. Use simple ATS-friendly formatting.", "Portfolio", 3),
        (6, "Block 3  14:00–16:00",  "LinkedIn profile setup",
         "Update LinkedIn headline, about section, skills, and experience. Add 'Open to Work'.", "Job Search", 4),
        (6, "Evening  18:00–20:00",  "Review & JARVIS check-in",
         "Save resume version 1 to data/resumes/. Log today's work.", "Review", 5),

        # ── DAY 7 ── VAPT & Security Testing Introduction
        (7, "Morning  07:00–09:00",  "Penetration testing methodology",
         "Study the 5 phases: Recon, Scanning, Exploitation, Post-Exploitation, Reporting.", "Learning", 1),
        (7, "Block 1  09:00–11:00",  "Burp Suite basics",
         "Open Burp Suite Community Edition. Learn the proxy, repeater, and spider tabs.", "Lab / Practical", 2),
        (7, "Block 2  11:00–13:00",  "TryHackMe — Burp Suite basics room",
         "Complete TryHackMe 'Burp Suite: The Basics' room.", "Lab / Practical", 3),
        (7, "Block 3  14:00–16:00",  "OWASP Top 10 overview",
         "Read the OWASP Top 10 (owasp.org). Understand injection, broken auth, IDOR, XSS.", "Learning", 4),
        (7, "Evening  18:00–20:00",  "Review & JARVIS check-in",
         "Could you explain a SQL injection attack in an interview? Write a 3-sentence answer.", "Review", 5),

        # ── DAY 8 ── IT & Application Support Skills
        (8, "Morning  07:00–09:00",  "ITIL framework basics",
         "Study Incident, Problem, Change Management concepts. Know the difference between them.", "Learning", 1),
        (8, "Block 1  09:00–11:00",  "Ticketing systems — ServiceNow / Jira overview",
         "Watch a free ServiceNow or Jira tutorial. Understand ticket lifecycle and SLA concepts.", "Learning", 2),
        (8, "Block 2  11:00–13:00",  "SQL basics for log analysis",
         "Practice SELECT, WHERE, ORDER BY, GROUP BY, COUNT on a sample database (use DB Browser for SQLite).", "Lab / Practical", 3),
        (8, "Block 3  14:00–16:00",  "Application monitoring concepts",
         "Study uptime monitoring, latency, error rates, alerting. Research tools: Grafana, Nagios, Zabbix.", "Learning", 4),
        (8, "Evening  18:00–20:00",  "Review & JARVIS check-in",
         "Write a one-paragraph summary of ITIL incident management in your own words.", "Review", 5),

        # ── DAY 9 ── Final Prep & Day 10 Launch Readiness ──
        (9, "Morning  07:00–09:00",  "MILESTONE: Day 10 launch checklist review",
         "Check: Resume ready? LinkedIn updated? Cover letter template drafted? TryHackMe progress noted?", "Admin / Setup", 1),
        (9, "Block 1  09:00–11:00",  "Draft cover letter templates (3 versions)",
         "Write SOC/Cybersecurity, IT Support, and Application Support cover letter templates. Save to data/notes/.", "Portfolio", 2),
        (9, "Block 2  11:00–13:00",  "Interview prep — common technical questions",
         "Prepare answers for: Tell me about yourself. What is a firewall? What is an IP address? Walk me through TCP/IP.", "Interview Prep", 3),
        (9, "Block 3  14:00–16:00",  "Recruiter outreach plan",
         "Identify 20 recruiters on LinkedIn in IT/Cybersecurity. Prepare a connection request message template.", "Job Search", 4),
        (9, "Evening  18:00–20:00",  "🚀 LAUNCH READY REVIEW — Day 9 complete",
         "Final check-in. Confirm all preparation milestones. Tomorrow you go live. Log this moment in JARVIS notes.", "Review", 5),

        # ── DAY 10 ── ACTIVE JOB SEARCH BEGINS ──
        (10, "Morning  07:00–09:00", "🚀 Day 10 — Active Job Search Begins",
         "Mission phase 2 starts today. Apply to 3–5 positions. Prioritise quality applications over volume.", "Job Search", 1),
        (10, "Block 1  09:00–11:00", "Submit first wave of applications",
         "Apply to 3 roles: 1 cybersecurity/SOC, 1 IT support, 1 app support. Log each in JARVIS Applications.", "Job Search", 2),
        (10, "Block 2  11:00–13:00", "LinkedIn recruiter outreach",
         "Send 10 personalised connection requests to IT/Cybersecurity recruiters. Keep the message brief and professional.", "Job Search", 3),
        (10, "Block 3  14:00–16:00", "Continue TryHackMe — SOC Level 1 path",
         "Complete 2 more rooms. Keep building verifiable credentials and portfolio evidence.", "Lab / Practical", 4),
        (10, "Evening  18:00–20:00", "Review responses & follow-up plan",
         "Check email and LinkedIn. Log any responses in JARVIS. Set follow-up reminders for 5 days out.", "Review", 5),
    ]

    # Days 11–50: Repeating pattern of Apply + Learn + Interview Prep + Review
    # We generate a structured template for each remaining day
    day_11_50_templates = [
        ("Morning  07:00–09:00",  "Morning review & priority setting",
         "Check JARVIS for follow-ups due. Set today's top 3 priorities.", "Admin / Setup", 1),
        ("Block 1  09:00–11:00",  "Apply to 3–5 positions",
         "Submit targeted applications. Tailor your resume keywords to match each job description.", "Job Search", 2),
        ("Block 2  11:00–13:00",  "Technical skill building",
         "Continue TryHackMe, Splunk training, or a lab exercise relevant to your target role.", "Lab / Practical", 3),
        ("Block 3  14:00–16:00",  "Interview prep or portfolio work",
         "Practise answering 5 technical interview questions aloud. Or add a lab write-up to your portfolio.", "Interview Prep", 4),
        ("Evening  18:00–20:00",  "Evening review & JARVIS check-in",
         "Log applications, hours, and labs. Check for recruiter replies. Update application statuses.", "Review", 5),
    ]

    for day in range(11, 51):
        for (tb, title, detail, cat, order) in day_11_50_templates:
            tasks.append((day, tb, title, detail, cat, order))

    conn.executemany(
        """INSERT INTO planner_tasks
           (day_number, time_block, task_title, task_detail, category, sort_order)
           VALUES (?, ?, ?, ?, ?, ?)""",
        tasks
    )
    conn.commit()
    conn.close()


def get_tasks_for_day(day_number: int):
    """Return all task rows for a given mission day, ordered by sort_order."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM planner_tasks WHERE day_number = ? ORDER BY sort_order",
        (day_number,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_completion_for_day(day_number: int, done_date: str) -> dict:
    """
    Return a dict mapping task_id -> done (0 or 1)
    for a specific mission day and calendar date.
    """
    conn = get_connection()
    task_ids = [
        r["id"] for r in
        conn.execute("SELECT id FROM planner_tasks WHERE day_number = ?", (day_number,)).fetchall()
    ]
    if not task_ids:
        conn.close()
        return {}
    placeholders = ",".join("?" * len(task_ids))
    rows = conn.execute(
        f"SELECT task_id, done FROM planner_completions WHERE task_id IN ({placeholders}) AND done_date = ?",
        task_ids + [done_date]
    ).fetchall()
    conn.close()
    return {r["task_id"]: r["done"] for r in rows}


def set_task_completion(task_id: int, done_date: str, done: bool):
    """Mark a single task as done or not-done for a specific calendar date."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO planner_completions (task_id, done_date, done)
           VALUES (?, ?, ?)
           ON CONFLICT(task_id, done_date) DO UPDATE SET done = excluded.done""",
        (task_id, done_date, 1 if done else 0)
    )
    conn.commit()
    conn.close()


def get_day_completion_pct(day_number: int, done_date: str) -> float:
    """Return 0.0–1.0 completion percentage for a mission day on a calendar date."""
    tasks = get_tasks_for_day(day_number)
    if not tasks:
        return 0.0
    completions = get_completion_for_day(day_number, done_date)
    done_count = sum(1 for t in tasks if completions.get(t["id"], 0) == 1)
    return done_count / len(tasks)


def update_planner_task(task_id: int, task_title: str, task_detail: str, time_block: str, category: str):
    """Edit the title/detail/time_block/category of an existing planner task."""
    conn = get_connection()
    conn.execute(
        """UPDATE planner_tasks
           SET task_title = ?, task_detail = ?, time_block = ?, category = ?
           WHERE id = ?""",
        (task_title, task_detail, time_block, category, task_id)
    )
    conn.commit()
    conn.close()


def add_planner_task(day_number: int, time_block: str, task_title: str, task_detail: str, category: str):
    """Add a new custom task to a mission day."""
    conn = get_connection()
    max_order = conn.execute(
        "SELECT MAX(sort_order) FROM planner_tasks WHERE day_number = ?", (day_number,)
    ).fetchone()[0] or 0
    conn.execute(
        """INSERT INTO planner_tasks (day_number, time_block, task_title, task_detail, category, sort_order)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (day_number, time_block, task_title, task_detail, category, max_order + 1)
    )
    conn.commit()
    conn.close()


def delete_planner_task(task_id: int):
    """Delete a planner task (and all its completion records)."""
    conn = get_connection()
    conn.execute("DELETE FROM planner_completions WHERE task_id = ?", (task_id,))
    conn.execute("DELETE FROM planner_tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()


def get_planner_history(start_day: int = 1, end_day: int = 50) -> list:
    """
    Return per-day completion summary for a range of mission days.
    Used for the weekly/overall progress view.
    Returns list of dicts: {day_number, total_tasks, done_tasks, pct}
    """
    conn = get_connection()
    rows = conn.execute(
        """SELECT pt.day_number,
                  COUNT(pt.id) as total_tasks,
                  COALESCE(SUM(pc.done), 0) as done_tasks
           FROM planner_tasks pt
           LEFT JOIN planner_completions pc ON pc.task_id = pt.id
           WHERE pt.day_number BETWEEN ? AND ?
           GROUP BY pt.day_number
           ORDER BY pt.day_number""",
        (start_day, end_day)
    ).fetchall()
    conn.close()
    result = []
    for r in rows:
        total = r["total_tasks"]
        done  = r["done_tasks"]
        result.append({
            "day_number": r["day_number"],
            "total_tasks": total,
            "done_tasks": done,
            "pct": round((done / total) * 100, 1) if total else 0.0,
        })
    return result


def force_reseed_planner():
    """
    Clears all planner_tasks and planner_completions and reseeds from scratch.
    Only called when the user explicitly requests it from the UI.
    WARNING: This deletes all planner completion history.
    """
    conn = get_connection()
    conn.execute("DELETE FROM planner_completions")
    conn.execute("DELETE FROM planner_tasks")
    conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('planner_tasks','planner_completions')")
    conn.commit()
    conn.close()
    _seed_planner_tasks_v2()


def _seed_planner_tasks_v2():
    """
    Seeds the NEW detailed 50-day plan.
    Days 1-9: specific, structured preparation tasks.
    Days 10-50: active job search repeating template.
    """
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM planner_tasks").fetchone()[0]
    if count > 0:
        conn.close()
        return

    tasks = [
        # ── DAY 1 ── Career baseline and technical assessment
        (1, "Block 1  09:00–11:00", "Review resume and career direction",
         "Open your current resume. List every role you are targeting. Write down your top 5 technical skills and your top 3 skill gaps.",
         "Admin / Setup", 1),
        (1, "Block 2  11:00–13:00", "Technical self-assessment",
         "Rate yourself 1-5 on: Networking, Windows admin, Linux, Cybersecurity basics, Troubleshooting. Be honest — this baseline guides the next 8 days.",
         "Review", 2),
        (1, "Block 3  14:00–16:00", "Organise career notes and evidence folders",
         "Create folders: data/resumes/, data/notes/, data/portfolio/. Save your current resume. Start a notes file for each skill area.",
         "Admin / Setup", 3),
        (1, "Evening  18:00–20:00", "Day 1 review and JARVIS check-in",
         "Log your self-assessment scores in JARVIS notes. Identify your top 3 weak areas to focus on this week.",
         "Review", 4),

        # ── DAY 2 ── Networking fundamentals
        (2, "Morning  07:00–09:00", "IP addressing and subnetting basics",
         "Study IPv4 addressing, subnet masks, CIDR notation. Practice reading /24, /16, /8 networks. Use Cisco Skills for All (free).",
         "Learning", 1),
        (2, "Block 1  09:00–11:00", "DNS, DHCP, TCP, UDP and common ports",
         "Understand how DNS resolves names. How DHCP assigns IPs. Difference between TCP and UDP. Memorise ports: 22 SSH, 80 HTTP, 443 HTTPS, 3389 RDP, 53 DNS, 25 SMTP.",
         "Learning", 2),
        (2, "Block 2  11:00–13:00", "Routing, gateways, HTTP and HTTPS",
         "Understand default gateways, routing tables, and what happens when you open a website. Study HTTP request-response cycle.",
         "Learning", 3),
        (2, "Block 3  14:00–16:00", "Windows networking commands practice",
         "Open CMD and practice: ipconfig, ipconfig /all, ping, tracert, nslookup, netstat -an. Document each command output.",
         "Lab / Practical", 4),
        (2, "Evening  18:00–20:00", "Networking review and notes",
         "Write a one-page networking summary in your own words. What would you say if asked 'explain how DNS works' in an interview?",
         "Review", 5),

        # ── DAY 3 ── Windows and IT Support
        (3, "Morning  07:00–09:00", "Windows troubleshooting methodology",
         "Learn the structured approach: define, reproduce, isolate, resolve, document. Apply it to 3 hypothetical scenarios.",
         "Learning", 1),
        (3, "Block 1  09:00–11:00", "User accounts, permissions and services",
         "Study local vs domain accounts, UAC, NTFS permissions. Use Computer Management to view users and groups. Study services: start, stop, automatic vs manual.",
         "Lab / Practical", 2),
        (3, "Block 2  11:00–13:00", "Event Viewer and Task Manager",
         "Open Event Viewer. Find System and Application logs. Identify an error or warning. Use Task Manager to view processes, CPU and memory usage.",
         "Lab / Practical", 3),
        (3, "Block 3  14:00–16:00", "Device Manager and system troubleshooting",
         "Review Device Manager for driver issues. Practice: msconfig, msinfo32, resmon. Run sfc /scannow in an elevated CMD.",
         "Lab / Practical", 4),
        (3, "Evening  18:00–20:00", "IT Support interview preparation",
         "Prepare answers to: How do you troubleshoot a PC that cannot connect to the internet? Walk me through resetting a user password in Windows.",
         "Interview Prep", 5),

        # ── DAY 4 ── Linux fundamentals
        (4, "Morning  07:00–09:00", "Linux file system navigation",
         "Study the Linux directory structure: /, /home, /etc, /var, /tmp, /usr. Practice cd, ls -la, pwd, mkdir, touch, cp, mv, rm.",
         "Learning", 1),
        (4, "Block 1  09:00–11:00", "File permissions, ownership and processes",
         "Understand rwx permissions, chmod numeric and symbolic. Study chown. Use ps aux, top, kill to manage processes.",
         "Lab / Practical", 2),
        (4, "Block 2  11:00–13:00", "Services, logs and shell commands",
         "Use systemctl start/stop/status/enable. Read /var/log/syslog and /var/log/auth.log. Use grep, cat, tail -f, find, man.",
         "Lab / Practical", 3),
        (4, "Block 3  14:00–16:00", "Linux practical exercises",
         "Complete TryHackMe Linux Fundamentals Room 1 (free). If no VM, use the in-browser terminal on TryHackMe.",
         "Lab / Practical", 4),
        (4, "Evening  18:00–20:00", "Linux review and notes",
         "Write 10 Linux commands you learned today with a one-line description of each. Save to data/notes/linux_commands.txt",
         "Review", 5),

        # ── DAY 5 ── Cybersecurity and SOC fundamentals
        (5, "Morning  07:00–09:00", "CIA triad, threats, vulnerabilities and risk",
         "Study Confidentiality, Integrity, Availability. Understand the difference between a threat, vulnerability and risk. Study common attack types: phishing, ransomware, MITM.",
         "Learning", 1),
        (5, "Block 1  09:00–11:00", "Malware, incident response and SOC workflows",
         "Study malware types: virus, worm, trojan, ransomware, spyware. Understand a basic IR lifecycle: Identify, Contain, Eradicate, Recover, Review.",
         "Learning", 2),
        (5, "Block 2  11:00–13:00", "SIEM, EDR and IDS/IPS concepts",
         "Understand what a SIEM does: collect logs, correlate events, raise alerts. Study EDR vs antivirus. Study IDS (detect) vs IPS (prevent).",
         "Learning", 3),
        (5, "Block 3  14:00–16:00", "TryHackMe Cybersecurity 101 path",
         "Register at TryHackMe (free). Start the Cybersecurity 101 path. Complete the first 2-3 rooms. Note: some rooms require a subscription.",
         "Lab / Practical", 4),
        (5, "Evening  18:00–20:00", "SOC interview preparation",
         "Prepare answers to: What is a SIEM? How would you investigate a phishing alert? What is the difference between IDS and IPS?",
         "Interview Prep", 5),

        # ── DAY 6 ── Logs and security investigation
        (6, "Morning  07:00–09:00", "Log interpretation and structure",
         "Understand log components: timestamp, source IP, destination IP, event type, user, action, result. Study Windows Event IDs: 4624 (login), 4625 (failed login), 4688 (process creation).",
         "Learning", 1),
        (6, "Block 1  09:00–11:00", "Identifying suspicious patterns in logs",
         "Study what makes a log entry suspicious: off-hours logins, repeated failures, unusual source IPs, privilege escalation. Use TryHackMe SIEM rooms.",
         "Learning", 2),
        (6, "Block 2  11:00–13:00", "Basic alert investigation exercise",
         "Take a sample set of logs (use TryHackMe or a free SIEM lab). Identify the timeline of an event. Determine source, target and action.",
         "Lab / Practical", 3),
        (6, "Block 3  14:00–16:00", "Splunk free training",
         "Register at Splunk Training (free tier). Begin Splunk Fundamentals 1. Note: free tier has limited access. Use what is available.",
         "Lab / Practical", 4),
        (6, "Evening  18:00–20:00", "Log investigation review",
         "Write a short incident summary from today's lab exercise: What happened? When? Who was involved? What action should be taken?",
         "Portfolio", 5),

        # ── DAY 7 ── Application Support and NOC troubleshooting
        (7, "Morning  07:00–09:00", "Structured troubleshooting methodology",
         "Study the OSI model as a troubleshooting framework. Learn to work top-down or bottom-up. Study the 5 Whys method.",
         "Learning", 1),
        (7, "Block 1  09:00–11:00", "DNS, connectivity and application failures",
         "Practice diagnosing: website unreachable, DNS not resolving, application not loading. Use ping, nslookup, tracert, curl.",
         "Lab / Practical", 2),
        (7, "Block 2  11:00–13:00", "Account, permission and resource issues",
         "Study common issues: access denied, locked accounts, permission errors, high CPU and memory. Document investigation steps.",
         "Learning", 3),
        (7, "Block 3  14:00–16:00", "Escalation and documentation practice",
         "Write an escalation note for a hypothetical production incident. Include: impact, timeline, steps taken, current status, next action.",
         "Portfolio", 4),
        (7, "Evening  18:00–20:00", "Application Support interview preparation",
         "Prepare answers to: How do you handle a production outage? A user reports an application is slow — what do you do?",
         "Interview Prep", 5),

        # ── DAY 8 ── Portfolio and professional readiness
        (8, "Morning  07:00–09:00", "GitHub profile and project review",
         "Open your GitHub profile. If empty, create an account. Plan one project to add: a troubleshooting script, a network scanner or a simple automation.",
         "Portfolio", 1),
        (8, "Block 1  09:00–11:00", "Write or improve a technical project",
         "Create or improve a project in GitHub. Add at minimum: a clear README, a description, and what problem it solves.",
         "Portfolio", 2),
        (8, "Block 2  11:00–13:00", "Write a technical case study",
         "Document one real or hypothetical technical scenario you resolved. Include: problem, investigation steps, root cause, solution, lessons learned.",
         "Portfolio", 3),
        (8, "Block 3  14:00–16:00", "Add evidence and screenshots",
         "Take screenshots of tools, terminals or labs you have used this week. Add them to data/portfolio/. Write one-line captions.",
         "Portfolio", 4),
        (8, "Evening  18:00–20:00", "Prepare project explanation",
         "Practice explaining your GitHub project or case study in under 2 minutes. Record yourself or write it out. This will be used in interviews.",
         "Interview Prep", 5),

        # ── DAY 9 ── Interview and application readiness
        (9, "Morning  07:00–09:00", "Technical interview question review",
         "Review and practise answers to: Tell me about yourself. What is your strongest technical skill? Why cybersecurity or IT support? How do you stay current with technology?",
         "Interview Prep", 1),
        (9, "Block 1  09:00–11:00", "Resume final review",
         "Read your resume as if you are the interviewer. Is every bullet point relevant? Are technical keywords present? Is the format clean and ATS-friendly?",
         "Job Search", 2),
        (9, "Block 2  11:00–13:00", "Professional introduction and LinkedIn",
         "Write a 60-second professional introduction. Update LinkedIn headline, about section and skills. Add Open to Work if comfortable.",
         "Job Search", 3),
        (9, "Block 3  14:00–16:00", "Prepare Day 10 application launch",
         "Research 10 live job postings for SOC Analyst, IT Support, App Support. Save links. Identify 5 recruiters to contact on LinkedIn. Set up job alerts.",
         "Job Search", 4),
        (9, "Evening  18:00–20:00", "🚀 LAUNCH READY REVIEW — Day 9 complete",
         "Confirm: Resume polished. LinkedIn updated. Cover letter template drafted. 10 job links saved. Recruiter list ready. You begin applying tomorrow.",
         "Review", 5),
    ]

    # Days 10-50: repeating daily template
    day_10_50_templates = [
        ("Morning  07:00–09:00", "Morning review and priority setting",
         "Check JARVIS for follow-ups due. Review yesterday's incomplete tasks. Set today's top 3 priorities: applications, learning and portfolio.",
         "Admin / Setup", 1),
        ("Block 1  09:00–11:00", "Apply to 3-5 positions",
         "Submit targeted applications. Match resume keywords to each job description. Log each application in JARVIS with follow-up dates.",
         "Job Search", 2),
        ("Block 2  11:00–13:00", "Technical skill development",
         "Continue your chosen learning path: TryHackMe, Splunk training, Microsoft Learn or Linux Journey. Aim to complete one room or module.",
         "Learning", 3),
        ("Block 3  14:00–16:00", "Portfolio or interview preparation",
         "Rotate between: writing a case study, improving GitHub, practising interview questions, documenting a lab exercise.",
         "Interview Prep", 4),
        ("Evening  18:00–20:00", "Evening review and JARVIS check-in",
         "Log applications, focus hours and labs completed. Check for recruiter replies. Update application statuses. Note one thing learned today.",
         "Review", 5),
    ]

    for day in range(10, 51):
        for (tb, title, detail, cat, order) in day_10_50_templates:
            tasks.append((day, tb, title, detail, cat, order))

    conn.executemany(
        """INSERT INTO planner_tasks
           (day_number, time_block, task_title, task_detail, category, sort_order)
           VALUES (?, ?, ?, ?, ?, ?)""",
        tasks
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# LEARNING RESOURCES
# ─────────────────────────────────────────────────────────────────────────────

RESOURCE_CATEGORIES = [
    "Networking & Packet Analysis",
    "Windows, Linux & Logs",
    "SOC, SIEM & Detection",
    "Blue-Team Labs & Alert Triage",
    "Phishing, IOCs & Incident Response",
    "Web Security & Fundamentals",
    "Portfolio & Job Search",
]


def _seed_learning_resources():
    """
    Seed the curated, strictly free-only learning library.
    If the table only has the old un-migrated 8-row seed with zero completions,
    upgrade it cleanly to the verified 21-resource free-only library.
    """
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM learning_resources").fetchone()[0]
    if count > 0:
        done_cnt = conn.execute("SELECT COUNT(*) FROM learning_resources WHERE done = 1").fetchone()[0]
        has_free_meta = conn.execute(
            "SELECT COUNT(*) FROM learning_resources WHERE exact_free_content != ''"
        ).fetchone()[0]
        if has_free_meta > 0 or done_cnt > 0:
            conn.close()
            return
        # Safe upgrade of unstarted legacy seed
        conn.execute("DELETE FROM learning_resources")
        conn.execute("DELETE FROM sqlite_sequence WHERE name = 'learning_resources'")

    # Format: (topic, skill_category, resource_title, provider, url, access_note,
    #          learning_obj, sequence_num, est_hours, practical_ex, expected_output,
    #          exact_free_content, relevant_days, registration_required, free_alternative, last_verified)
    resources = [
        # ── 1. Networking and packet analysis ──
        (
            "Packet Analysis", "Networking & Packet Analysis",
            "Wireshark User's Guide & Sample Captures",
            "Wireshark Foundation",
            "https://wiki.wireshark.org/SampleCaptures",
            "100% Free & Open Source — no limits",
            "Inspect DNS, TLS, HTTP, and TCP SYN packets using display filters on real public PCAPs.",
            1, 3.0,
            "Download a small public PCAP and apply `dns`, `tls`, and `tcp.flags.syn == 1 && tcp.flags.ack == 0` filters.",
            "2 Wireshark screenshots + list of domains and destination IPs.",
            "Public SampleCaptures wiki + official User's Guide (https://www.wireshark.org/docs/wsug_html_chunked/)",
            "Days 1, 8, 16, 44", "No",
            "Local ping/nslookup + tshark/PowerShell Get-NetTCPConnection", "2026-11-25"
        ),
        (
            "Networking Fundamentals", "Networking & Packet Analysis",
            "Practical Networking (DNS, Subnetting, TCP/IP)",
            "Practical Networking",
            "https://www.practicalnetworking.net",
            "100% Free articles and diagrams",
            "Master packet flow, NAT, routing, gateways, and subnetting without memorizing dry tables.",
            2, 3.0,
            "Read the Packet Traveling and Subnetting Mastery guides.",
            "Clear verbal explanation of DNS, TCP handshake, and routing.",
            "Free web articles, diagrams, and Subnetting Mastery series",
            "Days 1, 2, 8, 38", "No",
            "Professor Messer free Network+ videos", "2026-11-25"
        ),
        (
            "Networking & Ports", "Networking & Packet Analysis",
            "Professor Messer — Free Network+ Training Videos",
            "Professor Messer",
            "https://www.professormesser.com",
            "100% Free video library (optional paid notes/exams not needed)",
            "Learn ports (22, 53, 80, 443, 445, 3389), OSI model, firewalls, proxies, and VPNs.",
            3, 4.0,
            "Watch free Network+ N10-009 modules on Ports, Protocols, and Firewalls.",
            "One-page ports & protocols cheat sheet.",
            "Free on-site / YouTube Network+ video training course (paid exam vouchers not needed)",
            "Days 1, 8, 40", "No",
            "Cisco Skills for All — Networking Basics", "2026-11-25"
        ),
        (
            "Networking Basics", "Networking & Packet Analysis",
            "Cisco Skills for All — Networking Basics",
            "Cisco Networking Academy",
            "https://skillsforall.com/",
            "Free with free Cisco account — no credit card",
            "Structured interactive introduction to IP addressing, DNS, DHCP, and transport protocols.",
            4, 6.0,
            "Complete Networking Basics modules and verify with Windows CMD (`ipconfig`, `nslookup`).",
            "Ability to trace packet flow end-to-end.",
            "Free self-paced 'Networking Basics' course",
            "Days 1, 2, 8", "Yes (free account)",
            "Practical Networking + Professor Messer free videos", "2026-11-25"
        ),

        # ── 2. Windows, Linux and logs ──
        (
            "Windows Auditing & Support", "Windows, Linux & Logs",
            "Microsoft Learn — Security Auditing & Windows Docs",
            "Microsoft",
            "https://learn.microsoft.com/en-us/windows/security/threat-protection/auditing/security-auditing-overview",
            "100% Free official documentation",
            "Understand Event IDs 4624, 4625, 4634, 4648, 4672, 4688, 4720, 4728, 4732, 1102, 7045 and logon types.",
            5, 4.0,
            "Study 4624/4625 logon types (2, 3, 5, 10) and compare with local Event Viewer.",
            "Windows Security Event ID reference sheet.",
            "Official Windows Security Auditing Overview + Microsoft Learn IT Support modules",
            "Days 2, 11, 17, 26, 36, 40", "No (optional MS account)",
            "Built-in Windows Event Viewer + PowerShell Get-WinEvent", "2026-11-25"
        ),
        (
            "Endpoint Telemetry", "Windows, Linux & Logs",
            "Microsoft Sysinternals — Sysmon & SwiftOnSecurity Config",
            "Microsoft / SwiftOnSecurity",
            "https://learn.microsoft.com/en-us/sysinternals/downloads/sysmon",
            "100% Free official tool & open-source config",
            "Learn Sysmon Event IDs 1, 3, 7, 11, 13, 22 and parent-child process monitoring.",
            6, 2.5,
            "Review Sysmon documentation and SwiftOnSecurity's public sysmon-config.xml.",
            "Process-tree investigation notes for Event ID 1.",
            "Sysmon documentation + https://github.com/SwiftOnSecurity/sysmon-config",
            "Days 2, 12, 31", "No",
            "EVTX-ATTACK-SAMPLES Sysmon EVTX files", "2026-11-25"
        ),
        (
            "Public EVTX Datasets", "Windows, Linux & Logs",
            "EVTX-ATTACK-SAMPLES (Public Windows Attack Logs)",
            "sbousseaden (GitHub)",
            "https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES",
            "100% Free public GitHub repository",
            "Analyse real Windows & Sysmon attack telemetry safely on an 8 GB RAM Windows laptop without heavy VMs.",
            7, 4.0,
            "Inspect sample EVTX logs and build a 5–8 event timeline table.",
            "Day-02 timeline table with Time, Event ID, User, Source, Meaning, Conclusion.",
            "All public .evtx attack sample files in the repository",
            "Days 2, 8, 11, 12, 37, 44", "No",
            "Local Windows Event Viewer Security/System logs", "2026-11-25"
        ),
        (
            "Linux CLI & Logs", "Windows, Linux & Logs",
            "OverTheWire — Bandit Wargame",
            "OverTheWire",
            "https://overthewire.org/wargames/bandit/",
            "100% Free SSH wargame — no payment or subscription",
            "Build real confidence with Linux CLI navigation, permissions, `grep`, `sort`, `uniq`, and SSH.",
            8, 4.0,
            "Complete Bandit Levels 0–10 using free Windows SSH (`ssh` in PowerShell/CMD).",
            "Command notes saved in data/notes/.",
            "Bandit Levels 0–34 (100% free via SSH)",
            "Days 2, 13, 26", "No",
            "Linux Journey (https://linuxjourney.com/) + Linux man pages", "2026-11-25"
        ),
        (
            "Linux Fundamentals", "Windows, Linux & Logs",
            "Linux Journey & Official Linux Man Pages",
            "Linux Journey / kernel.org",
            "https://linuxjourney.com/",
            "100% Free — no account required",
            "Learn Linux filesystem, permissions, processes, services, `journalctl`, and shell commands.",
            9, 3.0,
            "Complete Grasshopper & Journeyman command/log sections.",
            "Linux log investigation note (`grep`, `awk`, `tail`, `journalctl`).",
            "All interactive lessons on linuxjourney.com + https://man7.org/linux/man-pages/",
            "Days 2, 13, 26", "No",
            "OverTheWire Bandit via Windows SSH", "2026-11-25"
        ),

        # ── 3. SOC, SIEM and detection ──
        (
            "SIEM Architecture", "SOC, SIEM & Detection",
            "Wazuh Open-Source Documentation",
            "Wazuh",
            "https://documentation.wazuh.com/current/quickstart.html",
            "100% Free & Open Source",
            "Understand SIEM/XDR architecture (indexer, server, dashboard, agents) and correlation ruleset.",
            10, 3.0,
            "Study Wazuh quickstart & ruleset docs; install locally ONLY if 8 GB RAM allows, otherwise use Splunk/Elastic free sandbox.",
            "SIEM architecture notes + 5-failed-logins detection logic.",
            "Quickstart + Ruleset Manual (https://documentation.wazuh.com/current/user-manual/ruleset/index.html)",
            "Day 3", "No",
            "Splunk Free Training + public EVTX log analysis", "2026-11-25"
        ),
        (
            "SIEM Search (SPL)", "SOC, SIEM & Detection",
            "Splunk Free Training Courses",
            "Splunk",
            "https://www.splunk.com/en_us/training/free-courses/overview.html",
            "Free tier — limited (free self-paced intro courses only; paid courses/certs not needed)",
            "Learn SIEM search fundamentals by time, host, user, IP, event ID, and basic dashboards.",
            11, 5.0,
            "Complete free intro/search courses and document failed-login SPL logic.",
            "Saved search logic + tuning explanation.",
            "Free Courses Overview (Intro to Splunk, Using Fields, Visualizations — free courses only)",
            "Days 3, 15", "Yes (free account)",
            "Elastic Free Training + local Python/PowerShell log search", "2026-11-25"
        ),
        (
            "SIEM & Elastic", "SOC, SIEM & Detection",
            "Elastic Free Training (Fundamentals)",
            "Elastic",
            "https://www.elastic.co/training",
            "Free tier — limited (free on-demand fundamentals only; paid certs/labs not needed)",
            "Understand indexing, parsing, KQL search, and SIEM dashboards.",
            12, 3.0,
            "Complete free Elastic Observability/Security fundamentals videos.",
            "Comparison note of SIEM search & correlation concepts.",
            "Free Quick Start / On-Demand Fundamentals courses only",
            "Days 3, 15", "Yes (free account)",
            "Wazuh Open-Source Docs + EVTX-ATTACK-SAMPLES", "2026-11-25"
        ),
        (
            "Detection Rules", "SOC, SIEM & Detection",
            "SigmaHQ Community Rules & Documentation",
            "SigmaHQ",
            "https://github.com/SigmaHQ/sigma",
            "100% Free & Open Source (GitHub)",
            "Read and write vendor-agnostic detection rules mapped to MITRE ATT&CK.",
            13, 2.5,
            "Inspect 3 Windows authentication/process rules in `rules/windows/` and draft 1 sample rule.",
            "Day-30 Sigma rule note.",
            "Public SigmaHQ rules repository & wiki",
            "Days 6, 30", "No",
            "Wazuh XML ruleset documentation", "2026-11-25"
        ),

        # ── 4. Blue-team labs and alert triage ──
        (
            "Blue-Team Labs", "Blue-Team Labs & Alert Triage",
            "CyberDefenders — Free Blue Team Labs",
            "CyberDefenders",
            "https://cyberdefenders.org/blueteam-ctf-challenges/",
            "Free tier — limited (filter by 'Free' challenges only; Pro labs not needed)",
            "Practise real PCAP, memory, and log forensics challenges at zero cost.",
            14, 4.0,
            "Filter for Free challenges and complete 1 beginner Network/Log lab.",
            "Write-up suitable for GitHub SOC portfolio.",
            "Free-tagged Blue Team CTF challenges only",
            "Days 4, 14, 16, 44", "Yes (free account)",
            "Wireshark SampleCaptures + EVTX-ATTACK-SAMPLES", "2026-11-25"
        ),
        (
            "SOC Triage Practice", "Blue-Team Labs & Alert Triage",
            "LetsDefend — Free Alerts & Blog Checklist",
            "LetsDefend",
            "https://letsdefend.io",
            "Free tier — limited (limited free alerts/cases per month; VIP subscription not needed)",
            "Practise the Alert → Context → Evidence → Verdict → Action → Note triage workflow.",
            15, 3.0,
            "Triage 2 free alerts and review the free SOC Analyst Interview Questions blog.",
            "5 structured triage notes (Day 4 deliverable).",
            "Free-tier SOC alerts + free blog (https://letsdefend.io/blog/soc-analyst-interview-questions-0f436)",
            "Days 4, 7, 14, 20, 31, 35, 47", "Yes (free account)",
            "Blue Team Labs Online free challenges + EVTX-ATTACK-SAMPLES", "2026-11-25"
        ),
        (
            "Security Practice", "Blue-Team Labs & Alert Triage",
            "TryHackMe — Free Rooms Only",
            "TryHackMe",
            "https://tryhackme.com",
            "Free tier — limited (only rooms marked Free; do NOT purchase subscription for this mission)",
            "Use free browser-based terminals and Linux/SOC intro rooms without straining 8 GB RAM.",
            16, 4.0,
            "Complete only rooms explicitly labeled Free (e.g., Linux Fundamentals Part 1, free intro rooms).",
            "Notes & screenshots of free room exercises.",
            "Free-labeled rooms only + free interview prep blog",
            "Days 4, 7, 9, 13, 22, 39, 48", "Yes (free account)",
            "OverTheWire Bandit + CyberDefenders Free Labs", "2026-11-25"
        ),
        (
            "Blue-Team Challenges", "Blue-Team Labs & Alert Triage",
            "Blue Team Labs Online (BTLO) — Free Challenges",
            "Security Blue Team",
            "https://blueteamlabs.online/",
            "Free tier — limited (Free Challenges only; Pro investigations not needed)",
            "Reinforce log investigation and incident triage on free browser challenges.",
            17, 3.0,
            "Complete 1–2 Free-tagged investigations.",
            "Triage summary note.",
            "Challenges filtered to 'Free' only",
            "Days 4, 14, 20", "Yes (free account)",
            "EVTX-ATTACK-SAMPLES + Wireshark SampleCaptures", "2026-11-25"
        ),

        # ── 5. Phishing, IOC analysis and incident response ──
        (
            "Phishing & Email Headers", "Phishing, IOCs & Incident Response",
            "Google Messageheader & MXToolbox Header Analyzer",
            "Google / MXToolbox",
            "https://toolbox.googleapps.com/apps/messageheader/",
            "100% Free web tools — never paste private/confidential company emails",
            "Inspect From, Reply-To, Return-Path, Received hops, SPF, DKIM, and DMARC.",
            18, 2.0,
            "Analyse a public phishing header sample and enrich public IOCs on VirusTotal/AbuseIPDB/urlscan.io.",
            "IOC table with >=5 indicators (Day 5 deliverable).",
            "Google Messageheader + https://mxtoolbox.com/EmailHeaders.aspx + VirusTotal/AbuseIPDB/urlscan.io free lookups",
            "Days 5, 20", "No",
            "Manual header inspection in Notepad/VS Code", "2026-11-25"
        ),
        (
            "MITRE ATT&CK & IR", "Phishing, IOCs & Incident Response",
            "MITRE ATT&CK, ATT&CK Navigator & NIST SP 800-61r3",
            "MITRE / NIST",
            "https://attack.mitre.org",
            "100% Free official frameworks",
            "Map alerts to verified ATT&CK Technique IDs and follow NIST Incident Response phases.",
            19, 3.0,
            "Map Day 4 alerts in ATT&CK Navigator (https://mitre-attack.github.io/attack-navigator/) and write 1-page IR report.",
            "ATT&CK Navigator screenshot + 1-page incident report (Day 6).",
            "MITRE ATT&CK + Navigator + https://csrc.nist.gov/pubs/sp/800/61/r3/final",
            "Days 6, 31, 32, 37", "No",
            "Local Markdown ATT&CK mapping table", "2026-11-25"
        ),

        # ── 6. Web security and security fundamentals ──
        (
            "Web Security & VAPT", "Web Security & Fundamentals",
            "PortSwigger Web Security Academy & OWASP Top 10",
            "PortSwigger / OWASP",
            "https://portswigger.net/web-security",
            "100% Free learning content and interactive labs (Burp Community Edition is also free)",
            "Learn SQLi, XSS, IDOR, Broken Access Control, and HTTP request interception.",
            20, 4.0,
            "Complete Apprentice labs on SQLi/XSS and read OWASP Top 10 (https://owasp.org/www-project-top-ten/).",
            "Day-23 OWASP summary + Day-24 Burp/PortSwigger lab note.",
            "Free PortSwigger Academy labs + OWASP Top 10 / WSTG / Cheat Sheets + Hacker101 (https://www.hacker101.com/)",
            "Days 23, 24", "Yes (free PortSwigger account for labs)",
            "OWASP Top 10 & OWASP Cheat Sheet Series (no account needed)", "2026-11-25"
        ),

        # ── 7. Portfolio and job search ──
        (
            "Portfolio, SQL & Job Search", "Portfolio & Job Search",
            "GitHub Free, LinkedIn Free & SQLBolt",
            "GitHub / LinkedIn / SQLBolt",
            "https://github.com",
            "100% Free tiers (LinkedIn Premium not needed)",
            "Publish sanitized SOC/support write-ups on GitHub, run targeted job searches, and practise SQL log queries.",
            21, 3.0,
            "Publish 2–3 clean write-ups on GitHub, track applications in JARVIS, and complete SQLBolt lessons 1–10.",
            "Live GitHub portfolio + active job pipeline.",
            "GitHub free public repos + LinkedIn free job search + SQLBolt (https://sqlbolt.com/)",
            "Days 7, 9, 10–50, 25, 27, 41", "Yes (free accounts for GitHub/LinkedIn)",
            "Local Markdown portfolio in data/notes/ + local SQLite queries", "2026-11-25"
        ),
    ]

    conn.executemany(
        """INSERT INTO learning_resources
           (topic, skill_category, resource_title, provider, url, access_note,
            learning_obj, sequence_num, est_hours, practical_ex, expected_output,
            exact_free_content, relevant_days, registration_required, free_alternative, last_verified)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        resources
    )
    conn.commit()
    conn.close()


def get_all_resources(category_filter=None) -> list:
    """Return all learning resources, optionally filtered by skill_category."""
    conn = get_connection()
    if category_filter and category_filter != "All":
        rows = conn.execute(
            "SELECT * FROM learning_resources WHERE skill_category = ? ORDER BY sequence_num",
            (category_filter,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM learning_resources ORDER BY sequence_num"
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_resource(topic, skill_category, resource_title, provider, url,
                 access_note, learning_obj, sequence_num, est_hours,
                 practical_ex, expected_output,
                 exact_free_content="", relevant_days="", registration_required="No",
                 free_alternative="", last_verified="2026-11-25") -> None:
    """Add a new learning resource."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO learning_resources
           (topic, skill_category, resource_title, provider, url, access_note,
            learning_obj, sequence_num, est_hours, practical_ex, expected_output,
            exact_free_content, relevant_days, registration_required, free_alternative, last_verified)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (topic, skill_category, resource_title, provider, url, access_note,
         learning_obj, sequence_num, est_hours, practical_ex, expected_output,
         exact_free_content, relevant_days, registration_required, free_alternative, last_verified)
    )
    conn.commit()
    conn.close()


def update_resource(resource_id: int, topic=None, skill_category=None,
                    resource_title=None, provider=None, url=None,
                    access_note=None, learning_obj=None, sequence_num=None,
                    est_hours=None, practical_ex=None, expected_output=None,
                    done=None, personal_notes=None,
                    exact_free_content=None, relevant_days=None,
                    registration_required=None, free_alternative=None,
                    last_verified=None) -> None:
    """Update fields of an existing learning resource. Only non-None values are updated."""
    conn = get_connection()
    fields = {
        "topic": topic,
        "skill_category": skill_category,
        "resource_title": resource_title,
        "provider": provider,
        "url": url,
        "access_note": access_note,
        "learning_obj": learning_obj,
        "sequence_num": sequence_num,
        "est_hours": est_hours,
        "practical_ex": practical_ex,
        "expected_output": expected_output,
        "done": done,
        "personal_notes": personal_notes,
        "exact_free_content": exact_free_content,
        "relevant_days": relevant_days,
        "registration_required": registration_required,
        "free_alternative": free_alternative,
        "last_verified": last_verified,
    }
    updates = {k: v for k, v in fields.items() if v is not None}
    if not updates:
        conn.close()
        return
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [resource_id]
    conn.execute(f"UPDATE learning_resources SET {set_clause} WHERE id = ?", values)
    conn.commit()
    conn.close()


def delete_resource(resource_id: int) -> None:
    """Delete a learning resource by ID."""
    conn = get_connection()
    conn.execute("DELETE FROM learning_resources WHERE id = ?", (resource_id,))
    conn.commit()
    conn.close()


def toggle_resource_done(resource_id: int, done: bool) -> None:
    """Mark a learning resource as done or not done."""
    conn = get_connection()
    conn.execute(
        "UPDATE learning_resources SET done = ? WHERE id = ?",
        (1 if done else 0, resource_id)
    )
    conn.commit()
    conn.close()


def get_resource_summary() -> dict:
    """Return total and done counts, overall and per category."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM learning_resources").fetchone()[0]
    done  = conn.execute("SELECT COUNT(*) FROM learning_resources WHERE done = 1").fetchone()[0]
    rows  = conn.execute(
        """SELECT skill_category,
                  COUNT(*) as total,
                  SUM(done) as done_count
           FROM learning_resources
           GROUP BY skill_category"""
    ).fetchall()
    conn.close()
    by_category = {
        r["skill_category"]: {"total": r["total"], "done": r["done_count"] or 0}
        for r in rows
    }
    return {
        "total": total,
        "done": done,
        "by_category": by_category,
    }


# ─────────────────────────────────────────────────────────────────────────────
# PORTFOLIO
# ─────────────────────────────────────────────────────────────────────────────

PORTFOLIO_CATEGORIES = [
    "GitHub Project",
    "Technical Case Study",
    "Troubleshooting Report",
    "Security Investigation",
    "Lab Write-Up",
    "Screenshot / Evidence",
    "Documentation",
    "Other",
]

PORTFOLIO_STATUSES = [
    "In Progress",
    "Complete",
    "Needs Improvement",
]


def get_all_portfolio_items(category_filter=None, status_filter=None) -> list:
    """Return all portfolio items, optionally filtered by category and/or status."""
    conn = get_connection()
    query = "SELECT * FROM portfolio_items WHERE 1=1"
    params = []
    if category_filter and category_filter != "All":
        query += " AND category = ?"
        params.append(category_filter)
    if status_filter and status_filter != "All":
        query += " AND status = ?"
        params.append(status_filter)
    query += " ORDER BY created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_portfolio_item(title, category, description, evidence_url,
                       skills_shown, status, date_completed, personal_notes) -> None:
    """Add a new portfolio item."""
    conn = get_connection()
    conn.execute(
        """INSERT INTO portfolio_items
           (title, category, description, evidence_url, skills_shown,
            status, date_completed, personal_notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (title, category, description, evidence_url, skills_shown,
         status, date_completed, personal_notes)
    )
    conn.commit()
    conn.close()


def update_portfolio_item(item_id: int, title, category, description,
                          evidence_url, skills_shown, status,
                          date_completed, personal_notes) -> None:
    """Update all fields of an existing portfolio item."""
    conn = get_connection()
    conn.execute(
        """UPDATE portfolio_items
           SET title = ?, category = ?, description = ?, evidence_url = ?,
               skills_shown = ?, status = ?, date_completed = ?, personal_notes = ?
           WHERE id = ?""",
        (title, category, description, evidence_url, skills_shown,
         status, date_completed, personal_notes, item_id)
    )
    conn.commit()
    conn.close()


def delete_portfolio_item(item_id: int) -> None:
    """Delete a portfolio item by ID."""
    conn = get_connection()
    conn.execute("DELETE FROM portfolio_items WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()


def get_portfolio_summary() -> dict:
    """Return total items, completed items, and categories covered."""
    conn = get_connection()
    total     = conn.execute("SELECT COUNT(*) FROM portfolio_items").fetchone()[0]
    completed = conn.execute(
        "SELECT COUNT(*) FROM portfolio_items WHERE status = 'Complete'"
    ).fetchone()[0]
    rows = conn.execute(
        "SELECT DISTINCT category FROM portfolio_items"
    ).fetchall()
    conn.close()
    categories = [r["category"] for r in rows]
    return {
        "total": total,
        "completed": completed,
        "categories_covered": categories,
    }


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD AGGREGATE
# ─────────────────────────────────────────────────────────────────────────────

def get_dashboard_summary(today: str, mission_day: int) -> dict:
    """
    Returns a single dict of all numbers needed by Mission Control.
    """
    conn = get_connection()
    # Applications
    app_rows = conn.execute("SELECT status, COUNT(*) as cnt FROM applications GROUP BY status").fetchall()
    app_summary = {r["status"]: r["cnt"] for r in app_rows}
    # Resources
    total_res = conn.execute("SELECT COUNT(*) FROM learning_resources").fetchone()[0]
    done_res  = conn.execute("SELECT COUNT(*) FROM learning_resources WHERE done=1").fetchone()[0]
    # Portfolio
    total_port = conn.execute("SELECT COUNT(*) FROM portfolio_items").fetchone()[0]
    done_port  = conn.execute("SELECT COUNT(*) FROM portfolio_items WHERE status='Complete'").fetchone()[0]
    # Planner for today
    tasks_today = conn.execute(
        "SELECT COUNT(*) FROM planner_tasks WHERE day_number=?", (mission_day,)
    ).fetchone()[0]
    done_today = conn.execute(
        """SELECT COUNT(*) FROM planner_completions pc
           JOIN planner_tasks pt ON pc.task_id=pt.id
           WHERE pt.day_number=? AND pc.done_date=? AND pc.done=1""",
        (mission_day, today)
    ).fetchone()[0]
    # Follow-ups
    followups = conn.execute(
        """SELECT COUNT(*) FROM applications
           WHERE follow_up_date!='' AND follow_up_date<=?
           AND status NOT IN ('Offer Received','Rejected','Withdrawn')""",
        (today,)
    ).fetchone()[0]
    conn.close()
    total_apps = sum(app_summary.values())
    return {
        "total_apps": total_apps,
        "recruiter_response": app_summary.get("Recruiter Response", 0),
        "interviews": app_summary.get("Interview Scheduled", 0) + app_summary.get("Interview Done", 0),
        "offers": app_summary.get("Offer Received", 0),
        "rejected": app_summary.get("Rejected", 0),
        "followups_due": followups,
        "total_resources": total_res,
        "done_resources": done_res,
        "total_portfolio": total_port,
        "done_portfolio": done_port,
        "tasks_today": tasks_today,
        "done_today": done_today,
        "pct_today": round((done_today / tasks_today) * 100) if tasks_today else 0,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 50-DAY MISSION CARDS (mission_days)
# ─────────────────────────────────────────────────────────────────────────────

MISSION_DAY_STATUSES = [
    "Not Started",
    "In Progress",
    "Completed",
    "Blocked",
]


def _seed_50day_mission_roadmap():
    """
    Populate mission_days (all 50 days) and upgrade planner_tasks to the
    50-day roadmap only if mission_days is empty.
    Preserves any existing planner_completions where possible.
    """
    conn = get_connection()
    count = conn.execute("SELECT COUNT(*) FROM mission_days").fetchone()[0]
    if count > 0:
        conn.close()
        return

    from roadmap_data import get_50_day_roadmap
    roadmap = get_50_day_roadmap()

    # Check if user has any actual completed tasks (done=1) before replacing template tasks
    done_count = conn.execute(
        "SELECT COUNT(*) FROM planner_completions WHERE done = 1"
    ).fetchone()[0]

    for day in roadmap:
        conn.execute(
            """INSERT OR IGNORE INTO mission_days
               (day_number, phase, mission_title, career_relevance, learning_target,
                step_by_step_method, time_allocation, resources_text, required_tools,
                deliverable, completion_criteria, checkpoint_questions, common_mistakes,
                interview_question, resume_relevance)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                day["day_number"], day["phase"], day["mission_title"],
                day["career_relevance"], day["learning_target"], day["step_by_step_method"],
                day["time_allocation"], day["resources_text"], day["required_tools"],
                day["deliverable"], day["completion_criteria"], day["checkpoint_questions"],
                day["common_mistakes"], day["interview_question"], day["resume_relevance"],
            )
        )

    # Upgrade planner_tasks to match the 50-day roadmap if no tasks were completed yet
    if done_count == 0:
        conn.execute("DELETE FROM planner_completions")
        conn.execute("DELETE FROM planner_tasks")
        conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('planner_tasks','planner_completions')")
        for day in roadmap:
            for idx, task in enumerate(day["tasks"], start=1):
                tb, title, detail, cat, est_min, res_url, exp_out = task
                conn.execute(
                    """INSERT INTO planner_tasks
                       (day_number, time_block, task_title, task_detail, category,
                        sort_order, est_minutes, resource_url, expected_output)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (day["day_number"], tb, title, detail, cat, idx, est_min, res_url, exp_out)
                )

    conn.commit()
    conn.close()


def get_mission_day(day_number: int):
    """Return the full 19-field mission card dict for a given day (1-50)."""
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM mission_days WHERE day_number = ?", (day_number,)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def update_mission_day_state(day_number: int, status: str, personal_notes: str, blocker_next_action: str):
    """Persist status, personal notes, and blocker/next action for a mission day."""
    conn = get_connection()
    conn.execute(
        """UPDATE mission_days
           SET status = ?, personal_notes = ?, blocker_next_action = ?
           WHERE day_number = ?""",
        (status, personal_notes, blocker_next_action, day_number)
    )
    conn.commit()
    conn.close()


def auto_start_mission_day(day_number: int):
    """Move a day from 'Not Started' to 'In Progress' when a task is checked."""
    conn = get_connection()
    conn.execute(
        """UPDATE mission_days
           SET status = 'In Progress'
           WHERE day_number = ? AND status = 'Not Started'""",
        (day_number,)
    )
    conn.commit()
    conn.close()


def get_mission_wide_progress() -> dict:
    """
    Calculate real mission-wide progress from SQLite:
    - total_tasks / completed_tasks across all 50 days
    - completed_days / total_days explicitly marked 'Completed'
    - in_progress_days / blocked_days
    """
    conn = get_connection()
    total_tasks = conn.execute("SELECT COUNT(*) FROM planner_tasks").fetchone()[0]
    completed_tasks = conn.execute(
        "SELECT COUNT(DISTINCT task_id) FROM planner_completions WHERE done = 1"
    ).fetchone()[0]
    total_days = conn.execute("SELECT COUNT(*) FROM mission_days").fetchone()[0] or 50
    completed_days = conn.execute(
        "SELECT COUNT(*) FROM mission_days WHERE status = 'Completed'"
    ).fetchone()[0]
    in_progress_days = conn.execute(
        "SELECT COUNT(*) FROM mission_days WHERE status = 'In Progress'"
    ).fetchone()[0]
    blocked_days = conn.execute(
        "SELECT COUNT(*) FROM mission_days WHERE status = 'Blocked'"
    ).fetchone()[0]
    conn.close()
    return {
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "tasks_pct": round((completed_tasks / total_tasks) * 100, 1) if total_tasks else 0.0,
        "total_days": total_days,
        "completed_days": completed_days,
        "days_pct": round((completed_days / total_days) * 100, 1) if total_days else 0.0,
        "in_progress_days": in_progress_days,
        "blocked_days": blocked_days,
    }


def add_planner_task_full(day_number: int, time_block: str, task_title: str, task_detail: str,
                          category: str, est_minutes: int = 45, resource_url: str = "", expected_output: str = ""):
    """Add a new custom task with duration, resource URL, and expected output."""
    conn = get_connection()
    max_order = conn.execute(
        "SELECT MAX(sort_order) FROM planner_tasks WHERE day_number = ?", (day_number,)
    ).fetchone()[0] or 0
    conn.execute(
        """INSERT INTO planner_tasks
           (day_number, time_block, task_title, task_detail, category,
            sort_order, est_minutes, resource_url, expected_output)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (day_number, time_block, task_title, task_detail, category,
         max_order + 1, est_minutes, resource_url, expected_output)
    )
    conn.commit()
    conn.close()
