FROM acait/django-container:1.1.7 as app-container

USER root
ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
	libpq-dev \
	postgresql postgresql-contrib odbc-postgresql \
	unixodbc-dev


USER acait
ADD --chown=acait:acait retention_data_pipeline/VERSION /app/retention_data_pipeline/
ADD --chown=acait:acait setup.py /app/
ADD --chown=acait:acait requirements.txt /app/
RUN . /app/bin/activate && pip install -r requirements.txt

ADD --chown=acait:acait . /app/
ADD --chown=acait:acait docker/ project/


FROM acait/django-test-container:1.0.35 as app-test-container
COPY --from=app-container /app/ /app/
COPY --from=app-container /static/ /static/


USER root
RUN apt-get -y install \
	unixodbc unixodbc-dev \
	freetds-dev freetds-bin \
	tdsodbc

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt install -y \
	software-properties-common \
	libxml2-dev libcurl4-openssl-dev libssl-dev

RUN apt-key adv \
	--keyserver keyserver.ubuntu.com \
	--recv-keys E298A3A825C0D65DFD57CBB651716619E084DAB9
RUN add-apt-repository 'deb https://cloud.r-project.org/bin/linux/ubuntu bionic-cran40/'
RUN apt update && apt install -y \
	r-base
RUN R -e "install.packages('pacman')"

# v installs requirements for R - can be really time consuming and not great for testing.
# currently checked for/ installed within R scripts
# RUN R -e "install.packages(c('odbc', 'optparse', 'dbplyr', 'dplyr', 'readr'), quiet=T, verbose=T)"

# puts our edw config where it should default
ADD /db_config/ /etc/

# puts env vars somewhere cron can access them
RUN env >> /etc/environment
