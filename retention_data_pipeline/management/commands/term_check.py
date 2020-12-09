from django.core.management.base import BaseCommand
import os
import sys
import subprocess
import datetime
from crontab import CronTab
from uw_sws import term, models


class Command(BaseCommand):
    def handle(self, *args, **options):
        """
        Gets current term from SWS, compares to the last time RAD data was retrieved.
        If the quarter's changed, we run a script and set it to run again on
        the 10th day of the quarter and every Monday until all drops/ schedule changes
        should be recoreded in the SDB.
        """
        fetch_path = os.path.dirname(
            os.path.abspath('reference_term.txt')
        )

        # check reference .txt file with information for Rscript from the last
        # RAD data gather
        ref_file = open(fetch_path + "/reference_term.txt")
        ref_list = ref_file.readlines()
        ref_file.close()
        ref_list = [i.strip("\n") for i in ref_list]
        ref_term = ",".join(ref_list[0:2])

        # get current term from SWS
        sws_term = term.get_current_term()
        sws_year, sws_qtr = sws_term.term_label().split(",")
        # reformat SWS term
        term_dict = {"winter": 1, "spring": 2, "summer": 3, "autumn": 4}
        current_term = sws_year + "," + str(term_dict[sws_qtr])

        # if there was a term change
        if current_term != ref_term:

            # write new reference term with SWS current term.
            ref_list[0], ref_list[1] = current_term.split(",")
            new_reference = "\n".join(ref_list)
            ref_file = open(fetch_path + "/reference_term.txt", "w")
            ref_file.write(new_reference)
            ref_file.close()

            # get census day & last day to drop courses
            census_day = sws_term.census_day
            last_day_drop = sws_term.last_day_drop
            # check for error with SWS dates
            if census_day > last_day_drop:
                sys.exit("Error: census and/ or final drop date inconsistencies.")

            # input year and quarter for Rscript
            input_year = int(sws_year)
            input_qtr = int(term_dict[sws_qtr])

            # cron scheduling vars
            last_day_drop += datetime.timedelta(days=7)  # catch changes after drop date
            start_month = str(census_day.month)
            end_month = str(last_day_drop.month)
            start_day = str(census_day.day)
            end_day = str(last_day_drop.day)

            # fetch data from the SDB every monday at 12:00am between census day and last drop day
            # overwrite crontab
            cron_sched = "0 0 {} {} 1".format(  # needs to be changed, implement script for start/end dates
                "-".join([start_day, end_day]), "-".join([start_month, end_month])
            )
            command = '. /root/.profile; Rscript --vanilla "{}fetch_sdb_data.R -y {} -q {} -d {}"'.format(
                fetch_path, input_year, input_qtr, fetch_path
            )

            subprocess.call(command, shell=True)
            cron = CronTab(user="root")
            # cron.remove_all(
            #     "Rscript"
            # )  # removes previous quarter's job if it exists in crontab
            job = cron.new(command=command)
            job.setall(cron_sched)
            cron.write()
            subprocess.call("/usr/sbin/cron start", shell=True)

        else:
            sys.exit("No term change.")
