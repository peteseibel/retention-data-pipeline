import os
import pyodbc
import pandas
from django.conf import settings

DB = "UWSDBDataStore"


def get_day1_enrollments(year, quarter):
    """
    Returns a list of student system_keys enrolled on day one and EOP status
    """
    campus = 0
    db_query = """
    SELECT  *
    FROM    (
        SELECT
            CASE WHEN mm_spcl_program IN(1, 2, 13, 14, 16, 17, 31, 32, 33)
                THEN CAST(1 AS BIT)
                ELSE CAST(0 AS BIT)
            END AS eop_student,
            (mm.mm_year*10 + mm.mm_qtr) as yrq,
            ROW_NUMBER() OVER
            (PARTITION BY mm.mm_system_key ORDER BY mm.mm_system_key) AS rn,
            mm_system_key, mm.mm_year, mm.mm_qtr, mm_deg_level, mm_major_abbr
        FROM
            sec.sr_mini_master mm
        INNER JOIN sec.sr_mini_master_deg_program deg
            ON deg.mm_student_no = mm.mm_student_no
            AND deg.mm_year = mm.mm_year
            AND deg.mm_qtr = mm.mm_qtr
        WHERE
            mm.mm_year = {}
            AND mm.mm_qtr = {}
            AND mm.mm_proc_ind = 2
            AND deg.mm_branch = {}) as a
    WHERE  a.rn = 1
    """.format(
        year, quarter, campus
    )
    results = _run_query(DB, db_query)
    return results


def get_ts_courses(year, quarter):
    db_query = """
    SELECT
        ts_year,
        ts_quarter,
        course_no,
        dept_abbrev,
        section_id,
        sln
    FROM
        sec.time_schedule
    WHERE
        ts_year = {}
        AND ts_quarter = {}
    """.format(
        year, quarter
    )
    results = _run_query(DB, db_query)
    return results


def get_registrations(year, quarter):
    db_query = """
        SELECT
            system_key,
            regis_yr,
            regis_qtr,
            sln
        FROM
            sec.registration_courses
        WHERE
            regis_yr = {}
            AND regis_qtr = {}
            AND request_status in ('A', 'C', 'R')
        """.format(
        year, quarter
    )
    results = _run_query(DB, db_query)
    return results


def get_student_metadata():
    db_query = """
        SELECT
            system_key,
            uw_netid,
            student_no,
            student_name_lowc
        FROM
            sec.student_1
    """
    results = _run_query(DB, db_query)
    return results


def get_international_students():
    db_query = """
        SELECT
            SDBSrcSystemKey,
            InternationalStudentInd
        FROM EDWPresentation.sec.dimStudent
        WHERE
            InternationalStudentInd = 'Y'
    """
    results = _run_query(DB, db_query)
    return results


def get_majors(year, quarter):

    db_query = """
        #TODO: Determine relationship w/ mini_maser and write query
        """.format(
        year, quarter
    )
    results = _run_query(DB, db_query)
    return results


def _run_query(database, query):
    os.environ["FREETDSCONF"] = "db_config/freetds.conf"
    os.environ["ODBCSYSINI"] = "db_config"

    password = getattr(settings, "EDW_PASSWORD")
    user = getattr(settings, "EDW_USER")
    server = getattr(settings, "EDW_SERVER")
    constring = (
        "Driver={FreeTDS};"
        f"SERVERNAME={server};"
        f"Database={database};"
        "Port=1433;"
        "TDS_Version=7.2;"
        f"UID={user};"
        f"PWD={password}"
    )
    con = pyodbc.connect(constring)
    df = pandas.read_sql(query, con)
    return df
