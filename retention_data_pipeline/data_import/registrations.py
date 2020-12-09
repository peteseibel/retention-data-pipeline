from retention_data_pipeline.models import Student
from retention_data_pipeline.dao.edw import (
    get_day1_enrollments,
    get_student_metadata,
    get_international_students,
)


def get_students_for_term(year, quarter):
    _get_sr_mini_master_students(year, quarter)


def _get_sr_mini_master_students(year, quarter):
    """
    Queries the sr_mini_master table and gets active students for a given term
    Also includes EOP status
    """
    students = get_day1_enrollments(year, quarter)
    intl_students = get_international_students()
    student_data = get_student_metadata()

    student_models = []
    for index, row in students.iterrows():
        major = row["mm_major_abbr"]
        system_key = row["mm_system_key"]
        is_intl = _get_intl_status(system_key, intl_students)
        netid, stu_num, name = _get_student_metadata(system_key, student_data)
        student = Student(
            year=year,
            quarter=quarter,
            system_key=system_key,
            is_eop=row["eop_student"],
            is_premajor=("PRE" in major or major == "EPRMJ"),
            is_international=is_intl,
            uw_netid=netid,
            student_no=stu_num,
            student_name_lowc=name,
        )
        student_models.append(student)
    Student.objects.bulk_create(student_models)


def _get_intl_status(system_key, intl_students):
    intl_matches = intl_students[intl_students.SDBSrcSystemKey == system_key]
    return len(intl_matches.index) > 0


def _get_student_metadata(system_key, student_data):
    student_matches = student_data[student_data.system_key == system_key]
    if len(student_matches.index > 0):
        data = student_matches.iloc[-1]
        netid = data["uw_netid"]
        stu_num = data["student_no"]
        name = data["student_name_lowc"]
    else:
        return None, None, None
    return netid, stu_num, name
