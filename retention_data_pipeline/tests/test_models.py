from django.test import TestCase
from retention_data_pipeline.models import StudentRegistration


class TestStudentRegistration(TestCase):
    def test_properties(self):
        stu_reg = StudentRegistration(
            year=2020,
            quarter=2,
            department_abbrev="CHEM",
            course_number=142,
            section_id="AA",
        )
        self.assertEqual(stu_reg.yrq, 20202)
        self.assertEqual(stu_reg.course_id, "2020-spring-CHEM-142-AA")
