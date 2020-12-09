#!/usr/bin/env Rscript

pacman::p_load(optparse, odbc, readr, dplyr, dbplyr)

optls <- list(make_option(c('-y', '--year'), default = as.numeric(2020),
                help = 'academic year [default = %default]. NOTE: requires corresponding provisioning file for year+quarter', metavar = 'numeric'),
            make_option(c('-q', '--quarter'), default = as.numeric(4),
                help = 'academic quarter (1/2/3/4) [default = %default], no support for summer terms', metavar = 'numeric'),
            make_option(c('-d', '--dir'), type = 'character', default = NULL,
                help = 'RELpath to project dir [default = %default]', metavar = 'character'),
            make_option(c('-t', '--testonly'), action = 'store_true', default = F,
                help = 'Override output to xxTEST.csv [default = %default].
                        WARNING: Non-test mode will overwrite existing files.'))
optprs <- OptionParser(option_list = optls)
opts <- parse_args(optprs)
if (is.null(opts$dir)){
    print_help(optprs)
    stop("At least one argument must be supplied (relative path to project)", call. = FALSE)
}
opts$dir <- paste0(opts$dir, "/")

setwd(opts$dir)

fun <- function() {
    con <- odbc::dbConnect(
    odbc::odbc(),
    dsn="edw",
    uid=Sys.getenv(c("EDW_USER")),
    pwd=Sys.getenv(c("EDW_PASSWORD"))
    )
    value <- tbl(
        con,
        in_schema(
            'sec',
            'student_1'
        )
    ) %>%
    dplyr::filter(
        uw_netid == strsplit(c(Sys.getenv(c("EDW_USER"))), "\\\\")[[1]][2]
    ) %>%
    collect()
    dbDisconnect(con)
    return(value)
}
f <- fun()

readr::write_lines(
    c(
        opts$year, opts$quarter,
        opts$dir, opts$testonly,
        {Sys.getenv(c("EDW_USER"))},
        f$student_no, f$admitted_for_yr,
        ""
    ),
    file=paste0(opts$dir, 'testing.txt'),
    append=T
)
# todo: (write +) run a script that checks the number of lines in testing.txt, and removes job from crontab once threshold is reached.


