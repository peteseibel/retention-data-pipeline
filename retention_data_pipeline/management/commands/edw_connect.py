from django.core.management.base import BaseCommand
from retention_data_pipeline.data_import.registrations import get_students_for_term


class Command(BaseCommand):
    def handle(self, *args, **options):
        # os.environ["FREETDSCONF"] = "db_config/freetds.conf"
        # os.environ["ODBCSYSINI"] = "db_config"
        #
        # password = getattr(settings, "EDW_PASSWORD")
        # user = getattr(settings, "EDW_USER")
        # server = getattr(settings, "EDW_SERVER")
        # constring = "Driver={FreeTDS};" \
        #             f"SERVERNAME={server};" \
        #             "Database=UWSDBDataStore;" \
        #             "Port=1433;" \
        #             "TDS_Version=7.2;" \
        #             f"UID={user};" \
        #             f"PWD={password}"
        # con = pyodbc.connect(constring)
        # cursor = con.cursor()
        # cursor.execute("select * from sec.sr_curric_code "
        #                "where curric_last_yr = 9999")
        # row = cursor.fetchone()
        # if row:
        #     print(row)
        # reg = edw.get_registrations(2020, 2)
        # print(reg.fetchone())
        # get_students_for_term(2020, 2)
        # enr = edw.get_international_students(2020, 2)
        # for index, row in enr.iterrows():
        #     print(row)
        # _add_international_status(2020, 2)
        # query = """
        # """
        # res = edw._run_query("UWSDBDataStore", query)
        # print(res)
        get_students_for_term(2020, 2)
