#!/bin/bash -e

### Variables ###
DATABASE_NAME="../../database.db"

JOB_START=0
JOB_END=9
JOB_INSTANCE_START=0
JOB_INSTANCE_END=9

function print(){
    echo -ne "$1"
}

print "Deleting old database... "
rm -f $DATABASE_NAME
print "done.\n"

### Create tables ###
print "Creating tables... "
sqlite3 $DATABASE_NAME << SQL_ENTRY_TAG_2

/*
*    job
*        id
*        credit
*        description
*
*    status
*        id
*        instance
*
*        client
*
*        accepted_datetime
*        returned_datetime
*
*    credit
*        client
*        credit
*/

CREATE TABLE job(
    id                  INTEGER PRIMARY KEY NOT NULL,
    credit              INTEGER,
    description         VARCHAR
);

CREATE TABLE status(
    id                  INTEGER NOT NULL,
    instance            INTEGER NOT NULL,

    client              VARCHAR,

    accepted_datetime   DATETIME,
    returned_datetime   DATETIME,

    PRIMARY KEY(id, instance)
);


CREATE TABLE credit(
    client              VARCHAR PRIMARY KEY,
    credit              INTEGER
);

CREATE TABLE translation(
    private_ip          VARCHAR,
    public_ip           VARCHAR PRIMARY KEY
);

SQL_ENTRY_TAG_2

print "done.\n"


### Create job binary ###
print "Replacing 'jobs' folder... "
rm -rf log*
rm -rf jobs 
mkdir jobs 
rm -rf ../client/jobs 
mkdir ../client/jobs 
print "done.\n"


print "Compiling 'job.c'... "
gcc -o job job.c > /dev/null
print "done.\n"


### Create jobs ###
print "Creating jobs:\n"
for i in `seq -f "%05g" $JOB_START $JOB_END`; do
    # Insert for job
    command="INSERT INTO job VALUES($i, 5, 'Copy 1000 times input');"
    print "\t$command\n"
    sqlite3 $DATABASE_NAME "$command"

    for j in `seq $JOB_INSTANCE_START $JOB_INSTANCE_END`; do
        # Insert for job instance
        command="INSERT INTO status VALUES($i, $j, NULL, NULL, NULL);"
        print "\t\t$command\n"
        sqlite3 $DATABASE_NAME "$command"

        # Create file
        print "\t\tPackaging job... "
        dir=jobs/$i$j
        mkdir $dir
        cp ./job $dir
        echo "$i" > $dir/jobInput
        tar czvf $dir.send $dir > /dev/null
        rm -rf $dir
        print "done.\n\n"
    done
done


### Insert clients ###
print "Creating clients.\n"
commands=(
    "INSERT INTO credit VALUES('128.164.160.198', 0);"
    "INSERT INTO credit VALUES('128.164.160.199', 0);"

    "INSERT INTO translation VALUES('10.8.0.10', '128.164.160.198');"
    "INSERT INTO translation VALUES('10.8.0.6',  '128.164.160.199');"
    )


for ((i=0;i<${#commands};i++)); do
    command=${commands[${i}]}
    sqlite3 $DATABASE_NAME "$command"; > /dev/null
    print "\t$command\n";
done


### Clean-up ###
print "Removing job binary... "
rm -f job
print "done.\n"
