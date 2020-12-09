#!/usr/bin/env Rscript

# TODO normalize paths

pacman::p_load(optparse, odbc, dplyr, dbplyr, readr)


## ARGS:
# project directory, ie if this is in ~/this_project/src-r then ../
# desired year, e.g. 2020
# desired qtr, e.g. 4
# (?) output path, with extension -- Assume this is 'data-raw/'

# TODO add file requirement checks before queries
# The output abbr, e.g. au20, will be built from the year + qtr input
optls <- list(make_option(c('-y', '--year'), default = as.numeric(2020),
                          help = 'academic year [default = %default]. NOTE: requires corresponding provisioning file for year+quarter', metavar = 'numeric'),
              make_option(c('-q', '--quarter'), default = as.numeric(4),
                          help = 'academic quarter (1/2/3/4) [default = %default], no support for summer terms', metavar = 'numeric'),
              make_option(c('-d', '--dir'), type = 'character', default = NULL,
                          help = 'RELpath to project dir [default = %default]', metavar = 'character'),
              make_option(c('-t', '--testonly'), action = 'store_true', default = T, # can set default F, although it won't write output.
                          help = 'Override output to xxTEST.csv [default = %default].
                          WARNING: Non-test mode will overwrite existing files.'))
optprs <- OptionParser(option_list = optls)
opts <- parse_args(optprs)
if (is.null(opts$dir)){
  print_help(optprs)
  stop("At least one argument must be supplied (relative path to project)", call. = FALSE)
}
# TODO ? remove redundancy from parser > local vars ?
# args <- commandArgs(trailingOnly = TRUE)
setwd(opts$dir)
cat('project directory: ', getwd(), fill = T)
year <- opts$year; cat('year: ', year, fill = T)
qtr <- opts$quarter; cat('qtr: ', qtr, fill = T)

file_prefix <- paste0(c('wi', 'sp', 'su', 'au')[qtr], year %% 100); cat(file_prefix, fill = T)
cat('out file abbr: ', file_prefix)
cat('test only? ', opts$testonly)

con <- dbConnect(
  odbc::odbc(),
  dsn='edw',
  UID=Sys.getenv(c("EDW_USER")),
  PWD=Sys.getenv(c("EDW_PASSWORD"))
)

# Enrollment --------------------------------------------------------------

#' Get enrollment data for year+quarter; include new freshman status and EOP

enr_d1 <- tbl(con, in_schema('sec', 'registration')) %>%    # actually registration for day < 1, not the enrollment from sr_mini_master
  filter(
    regis_yr == year,
    regis_qtr == qtr,
    regis_class <= 4,
    enroll_status > 0
  ) %>%
  mutate(
    yrq = regis_yr * 10 + regis_qtr,
    incoming_freshman = if_else(regis_class <= 1 & regis_ncr == 1, 1, 0)
  ) %>%
  # add student_1 data: EOP, sys key, netid, student no, name
  left_join( tbl(con, in_schema('sec', 'student_1') ) %>%
              select(
                system_key,
                uw_netid,
                student_no,
                student_name_lowc,
                spcl_program)
  ) %>%
  mutate(
    eop_student = if_else(
      spcl_program %in% c(1, 2, 13, 14, 16, 17, 31, 32, 33) |
      special_program %in% c(1, 2, 13, 14, 16, 17, 31, 32, 33), 1, 0
    )
  ) %>%
  select(
    system_key,
    uw_netid,
    student_no,
    student_name_lowc,
    regis_yr,
    regis_qtr,
    yrq,
    eop_student,
    regis_class,
    regis_ncr,
    enroll_status,
    incoming_freshman
  ) %>%
  distinct()

# collect STEM major codes, premajor students -----------------------------

#' Retrieve STEM majors using CIP codes from EDW.
#' Associate STEM codes with students' majors and flag premajor students.

# edw_cips <- tbl(con, in_schema('EDWPresentation.sec', 'dimCIPCurrent'))
edw_cips <- dbplyr::build_sql(
  con=con,
  "
  SELECT * FROM EDWPresentation.sec.dimCIPCurrent
  "
)
edw_cips <- DBI::dbGetQuery(con, edw_cips)

mjr_cips <- tbl(con, in_schema('sec', 'sr_major_code')) %>%
  filter(major_branch == 0) %>%
  left_join(edw_cips,
            copy = T,
            by = c('major_cip_code' = 'CIPCode')) %>%
  mutate(
    stem = if_else(FederalSTEMInd == 'Y', 1, 0),
    premajor = case_when(
    major_premaj == 'TRUE' ~ 1,                # caveat: logical types are text, despite what collection would indicate
    major_premaj_ext == 'TRUE' ~ 1,
    TRUE ~ 0)
  ) %>%
  select(
    major_abbr,
    stem,
    premajor
  ) %>%
  distinct()

majors <- tbl(con, in_schema('sec', 'student_1_college_major')) %>%
  filter(
    branch == 0,
    deg_level <= 1
  ) %>%
  semi_join(enr_d1) %>%
  left_join(
    mjr_cips,
    by = c('major_abbr' = 'major_abbr')
  ) %>%
  # now aggregate
  group_by(system_key) %>%
  summarize(
    stem = max(stem, na.rm = T),
    premajor = max(premajor, na.rm = T)
  ) %>%
  ungroup()

# # Seattle international students ------------------------------------------

#' International + undergraduate + filter to SEA campus only by major code
intl_stu <- dbplyr::build_sql(
  con=con,
  "
  SELECT * FROM EDWPresentation.sec.dimStudent
  "
)
intl_stu <- DBI::dbGetQuery(con, intl_stu) %>%
  filter(
    InternationalStudentInd == "Y",
    StudentClassGroupShortDesc == "UG"
  ) %>%
  semi_join(enr_d1, by = c('SDBSrcSystemKey' = 'system_key')) %>%
  mutate(international_student = if_else(InterNationalStudentInd == 'Y', 1, 0)) %>%
  select(
    system_key = SDBSrcSystemKey,
    international_student
  ) %>%
  # narrow down to SEA only w/ major code here
  semi_join(
    tbl(con, in_schema('sec', 'student_1_college_major')) %>%
      filter(
        branch == 0,
        deg_level %in% c(0, 1)
      )
  ) %>%
  distinct()

# registration courses on day 1 -------------------------------------------

#' Collect enrolled courses from the enrollment query
courses_d1 <- tbl(con, in_schema('sec', 'registration_courses')) %>%
  filter(request_status %in% c('A', 'C', 'R')) %>%
  semi_join(enr_d1) %>%
  select(
    system_key,
    regis_yr,
    regis_qtr,
    dept_abbrev = crs_curric_abbr,
    course_no = crs_number,
    section_id = crs_section_id
  ) %>%
  collect()


# collect and merge -------------------------------------------------------

#' Combine queries, beginning with enrollment
#' Then inner join with courses

dat <- enr_d1 %>%
  left_join(intl_stu) %>%
  left_join(majors) %>%
  filter(eop_student == 1 | international_student == 1 | premajor == 1 | incoming_freshman == 1) %>%
  collect()


# # Add ISS students
# # with correction should any also appear in other groups
# i <- iss_students[iss_students$system_key %in% dat$system_key,]
# iss_students <- iss_students[!(iss_students$system_key %in% i$system_key),]

# dat <- dat %>% bind_rows(iss_students)
# dat$isso[dat$system_key %in% i$system_key] <- 1

# dat <- dat %>% replace_na(list(incoming_freshman = 0,
#                                stem = 0,
#                                international_student = 0,
#                                premajor = 0,
#                                eop_student = 0,
#                                isso = 0))

# # collect/combine with courses
# courses_d1 <- courses_d1 %>% bind_rows(iss_student_courses)
# dat <- dat %>% inner_join(courses_d1)


# Now combine with Canvas users -------------------------------------------

# COURSES provisioning key format
# course_id: 2020-spring-B PHYS-119-B

# USERS provisioning key format
# login_id ~ uw_netid

# Trim total data, gen corresponding course key
dat <- dat %>%
  mutate_if(is.character, trimws) %>% # c('wi', 'sp', 'su', 'au')[qtr]
  mutate(
    course_id = paste(
      year,
      c('winter', 'spring', 'summer', 'autumn')[qtr],
      dept_abbrev,
      course_no,
      section_id,
      sep = "-"
    )
  ) %>%
  distinct()

# # Import provisioning tables
# # prov_users <- read_csv('data-raw/provisioning-current/users.csv')
# c_file <- paste0('data-raw/provisioning-current/courses_', file_prefix, '.csv')
# prov_courses <- read_csv(c_file) # %>% filter(status == 'active')

# # create course 'list' for python script
# filt_courses <- prov_courses[prov_courses$course_id %in% dat$course_id,]  # Not limiting this to active atm
# course_list <- unique(filt_courses$canvas_course_id)

# clist_file <- paste0('data-intermediate/', file_prefix, '-course-list.txt')
# dat_file <- paste0('data-intermediate/', file_prefix, '-netid-name-stunum-categories.csv')

if(isTRUE(opts$testonly)) {
  write_csv(dat, paste0('data-intermediate/', file_prefix, 'TEST.csv')) } else {
    write_lines(course_list, clist_file)
    write_csv(dat, dat_file)
  }

# TODO
# # # summer registration qtr -----------------------------------------------------
# #
# # reg_summer <- tbl(con, in_schema('sec', 'registration_courses')) %>%
# #   semi_join(now, copy = T, by = c('regis_yr' = 'current_yr',
# #                                   'regis_qtr' = 'current_qtr')) %>%
# #   filter(request_status %in% c('A', 'C', 'R')) %>%
# #   select(system_key, summer_term) %>%
# #   collect() %>%
# #   mutate(#qtr = 'summer',
# #          summer_term = if_else(summer_term == ' ', 'Full', summer_term)) %>%
# #   distinct() %>%
# #   arrange(system_key, summer_term)
# #
# # reg_summer <- aggregate(reg_summer$summer_term,
# #                         by = list(system_key = reg_summer$system_key),
# #                         paste, collapse = '-')
# # names(reg_summer)[2] <- 'summer'
#
# # write_csv(reg_summer, 'data-intermediate/summer-reg-terms.csv')



# cleanup -----------------------------------------------------------------

dbDisconnect(con)
