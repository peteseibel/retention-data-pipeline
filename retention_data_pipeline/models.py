from django.db import models

QUARTER_CHOICES = ((1, "Winter"), (2, "Spring"), (3, "Summer"), (4, "Autumn"))


class RawStudent(models.Model):
    CAMPUS_CHOICES = ((1, "Seattle"), (2, "Tacoma"), (3, "Bothell"))
    last_yr_enrolled = models.PositiveSmallIntegerField()
    last_qtr_enrolled = models.PositiveSmallIntegerField(
        default=1, choices=QUARTER_CHOICES
    )
    system_key = models.PositiveIntegerField()
    uw_netid = models.CharField(max_length=128)
    student_no = models.PositiveIntegerField()
    student_name_lowc = models.TextField()
    proc_ind = models.PositiveSmallIntegerField()
    spcl_program = models.PositiveSmallIntegerField()
    major_campus = models.PositiveSmallIntegerField(default=1, choices=CAMPUS_CHOICES)
    deg_level = models.PositiveSmallIntegerField()
    major_abbr = models.CharField(max_length=6)


class RawSection(models.Model):
    year = models.PositiveSmallIntegerField()
    quarter = models.PositiveSmallIntegerField(default=1, choices=QUARTER_CHOICES)
    course_no = models.PositiveSmallIntegerField()
    dept_abbrev = models.CharField(max_length=6)
    section_id = models.CharField(max_length=3)
    sln = models.PositiveIntegerField()


class Student(models.Model):
    year = models.PositiveSmallIntegerField()
    quarter = models.PositiveSmallIntegerField(default=1, choices=QUARTER_CHOICES)
    system_key = models.PositiveIntegerField()
    uw_netid = models.CharField(max_length=128, null=True)
    student_no = models.PositiveIntegerField(null=True)
    student_name_lowc = models.TextField(null=True)
    is_international = models.BooleanField(default=False)
    is_premajor = models.BooleanField(default=False)
    is_eop = models.BooleanField(default=False)

    class Meta:
        unique_together = [["year", "quarter", "system_key"]]


class StudentRegistration(models.Model):
    year = models.PositiveSmallIntegerField()
    quarter = models.PositiveSmallIntegerField(default=1, choices=QUARTER_CHOICES)
    department_abbrev = models.CharField(max_length=6)
    course_number = models.PositiveSmallIntegerField()
    section_id = models.CharField(max_length=2)
    system_key = models.PositiveIntegerField()
    uw_netid = models.CharField(max_length=128)
    student_no = models.PositiveIntegerField()
    student_name_lowc = models.TextField()
    is_international = models.BooleanField(default=False)
    is_premajor = models.BooleanField(default=False)
    is_eop = models.BooleanField(default=False)

    @property
    def course_id(self):
        return "{}-{}-{}-{}-{}".format(
            self.year,
            self.get_quarter_display().lower(),
            self.department_abbrev,
            self.course_number,
            self.section_id,
        )

    @property
    def yrq(self):
        return self.year * 10 + self.quarter
