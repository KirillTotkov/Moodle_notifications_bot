#!/bin/bash

pathProject=~/project
pathBackup=~/backup
dbUser=user_name
database=db_name

cd $pathProject && docker-compose exec -t db pg_dumpall -U $dbUser $database | gzip > $pathBackup/dump_`date +%d-%m-%Y"_"%H_%M_%S`.sql.gz