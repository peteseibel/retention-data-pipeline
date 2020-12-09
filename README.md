# retention-data-pipeline
App for getting data into RAD app

This is a docker image that connects to the EDW and a small Django app that fetches and stores data.


Using the container
1. Set environemntal variables for the EDW user and password, as well as an SWS authorization bearer token.

    `export EDW_USER="netid\\put_netid_here"`

    `export EDW_PASSWORD="password"`

    `export SWS_OAUTH_BEARER="token"`

2. Build and start the container

    `docker-compose up -d --build`

    Note: This step currently takes longer than it needs to, installing packages for R can be streamlined.


3. Connect to the container.
    Get the container id and connect to the shell on that container

    `docker ps`     This lists all containers, get the id from here

    `docker exec -u 0 -it [container ID] /bin/bash`

    Example:

    command:
    `docker ps`

    output:
    <pre>
        CONTAINER ID        IMAGE                         COMMAND                  CREATED             STATUS              PORTS                    NAMES
    770330ba50ed        retention-data-pipeline_app   "dumb-init --rewrite…"   6 minutes ago       Up 6 minutes        0.0.0.0:8000->8000/tcp   app
    </pre>

    command:
    `docker exec -u 0 -it 770330ba50ed /bin/bash`

    output (this is the container shell):
    `root@770330ba50ed:/app#`


4. Either be on the UW network physically or set up the Big IP VPN client to get a campus IP, EDW is restricted to on-campus networking only (this applies to the host running the docker container, eg your workstation)

5. Activate the virtualenv

    `source bin/activate`

6. Run the test commands to verify connections

    `./manage.py edw_connect`

    Should take ~30-90 seconds, will only output on error.  You can use the dbshell to see the locally stored data

    `./manage.py term_check_test`

    Runs a script that queries SWS for term info, checks against a local reference term, then will either initiate an R script that connects to the EDW & writes the parameters it's passed to a txt file once per minute or it will exit and return: 'No term change.'