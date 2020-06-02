# Redshift - Data warehouse project

This project exercises the use of:
- Python/ETL queries to turn a [3NF](https://en.wikipedia.org/wiki/Third_normal_form) schema into a [star schema](https://en.wikipedia.org/wiki/Star_schema)
- [AWS S3](https://aws.amazon.com/s3/) integration to [AWS Redshift](https://aws.amazon.com/redshift/) for parallel import of staging data
- Redshift for querying the imported data

## Pre-requisites

To satisfy the pre-requisites, we recommend that you use Infrastructure as Code to manage these resources. Tools like [AWS Cloudformation](https://aws.amazon.com/cloudformation/), [Terraform](https://www.terraform.io/) or [Pulumi](https://www.pulumi.com/) will make the provisioning/decomissioning of the Redshift cluster, s3 user and IAM user/roles easier to reproduce in the future.

1. AWS CLI

This will enable us to be authenticated in AWS. The installation guide can be found [here](https://aws.amazon.com/cli/).

2. AWS IAM role

For the Redshift cluster to read file from S3 buckets, you need to create a new IAM role that has `AmazonS3ReadOnlyAccess`.

This role will delegate S3 access to Redshift.  

Take note of the ARN (arn:aws:iam::[AWS ACCOUNT ID]:role/[ROLE NAME]) as you will need it when creating the cluster.

Note: this permission must be further restricted in terms of target resources but you can temporarily use that as a baseline if you accept not spending time on building fine-grained IAM policies and are comfortable with this temporary setup/cluster.

3. AWS IAM User

A new IAM user with programmatic access keys and console access is needed for this project.

The user will need the permission `AmazonRedshiftFullAccess` and a new policy. 

Create a new policy `redshift-passrole` that has the permission on IAM::PassRole. Here, the `PassRole` permission for this new user is needed in order to authorize Redshift to assume the previously created IAM role.

Do not use your root AWS account or an existing user to run this project as a security mistake can open access to someone else to your account.

Now that you've given console access to this new user, you can login in with it for the next pre-requirements.

/!\ Keep this information private and never expose it to anyone or in Git.

Note: this permission must be further restricted in terms of target resources and permission scope but you can temporarily use that as a baseline if you accept not spending time on building fine-grained IAM policies and are comfortable with this temporary setup/cluster.

3. AWS Security Group

We will restrict access to Redshift on our personal IP with a Security Group.

In the EC2 console, create a new security group. It's not ideal but for simplicity, put the security group in the default VPC that is already attached to your AWS account.

Add a rule to the security group as follows:

- Type: Custom TCP Rule.
- Protocol: TCP.
- Port Range: 5439. The default port for Amazon Redshift is 5439, but your port might be different. See note on determining your firewall rules on the earlier "AWS Setup Instructions" page in this lesson.
- Source: select Custom IP, then type your own IP with a `/32` at the end. You can find your own [public IP here](https://www.myip.com/). You may share the same public IP in the same service area where customers of your  Internet provider are, but this will limit who can access it..

4. AWS Redshift cluster

Create a Redshift cluster with the following information:

- Cluster identifier: redshift-cluster.
- Database name: dev.
- Database port: 5439.
- Master user name: awsuser.
- Master user password and Confirm password: password for the master user account.

4 nodes is recommended for this project. You can use the `dc2.large` EC2 instance as the cheapest option ($0.33/node/hour).  This will allow for 2 [slices per node](https://docs.aws.amazon.com/redshift/latest/dg/c_high_level_system_architecture.html) for parallelising ETL ingestion.

/!\ Keep this information private and never expose it to anyone or in Git.

In the additional configurations,

- Network and security > VPC security groups: select the VPC where your newly created Security group is.
- Cluster permissions > Role: specify the role ARN of the newly created role.
VPC security groups: redshift_security_group
Available IAM roles: myRedshiftRole

If you can't connect to the cluser, follow this [support guide](https://aws.amazon.com/premiumsupport/knowledge-center/cannot-connect-redshift-cluster/)

5. AWS S3 bucket

A new S3 bucket is needed for storing the datasets.

## Usage

### Structure & configuration

The project includes 3 main files:

- `create_table.py`: Python functions used to connect to Redshift and create, drop 
- `etl.py`: Python functions used to connect to Redshift and load staging tables in Redshift and then process that data into your analytics tables on Redshift.
- `sql_queries.py`: provides all SQL statements to `DROP`, `CREATE`, and `INSERT INTO` the fact and dimension tables used in the star schema

To interact with Redshift and S3, you will need to create a configuration file `dwh.cfg` and supply:

- the credentials to access Redshift
- AWS role that allows to read S3 buckets from Redshift
- S3 locations used for the datasets:

Rename `dwh.cfg-dist` into `dwh.cfg` needs to be in the root folder and structured as follows:

```ini
[CLUSTER]
HOST=
DB_NAME=
DB_USER=
DB_PASSWORD=
DB_PORT=

[IAM_ROLE]
ARN=''

[S3]
LOG_DATA='s3://mybucket/log_data'
LOG_JSONPATH='s3://mybucket/log_json_path.json'
SONG_DATA='s3://mybucket/song_data'
```

### Redshift ETL-ing

Once configured, execute the following commands to load the datasets and create the star schema:

```console
pip3 install -r requirements.txt
python3 create_tables.py
python3 etl.py
```

## Datasets

The project datasets are based on a subset from the [Million Song Dataset](https://labrosa.ee.columbia.edu/millionsong/).

A small subset of the data is available in the `data` folder.

### Songs data

You will need to store the data in a S3 bucket with the following structure:

- Song data: s3://mybucket/song_data
- Log data: s3://mybucket/log_data
- Log data json path: s3://mybucket/log_json_path.json

Each file is in JSON format and contains metadata about a song and the artist of that song.

The files are structured in a hierarchy of folders that follow the alphabetical order of the first three letters of each song's track ID. 

For example:

```bash
song_data/A/B/C/TRABCEI128F424C983.json
song_data/A/A/B/TRAABJL12903CDCF1A.json
```

A single song file as the following form:

```json
{
    "artist_id": "ARJNIUY12298900C91",
    "artist_latitude": null,
    "artist_location": "",
    "artist_longitude": null,
    "artist_name": "Adelitas Way",
    "duration": 213.9424,
    "num_songs": 1,
    "song_id": "SOBLFFE12AF72AA5BA",
    "title": "Scream",
    "year": 2009
}
```

### Log Dataset

The logs dataset is generated from this [event simulator](https://github.com/Interana/eventsim) based on the songs in the song dataset. It will be used as our simulation of activity logs from users listening to songs.

The log files are partitioned by year and month. For example,

```bash
log_data/2018/11/2018-11-12-events.json
log_data/2018/11/2018-11-13-events.json
```

A single log file as the following form:

```json
{
...
}
{
    "artist": null,
    "auth": "Logged In",
    "firstName": "Walter",
    "gender": "M",
    "itemInSession": 0,
    "lastName": "Frye",
    "length": null,
    "level": "free",
    "location": "San Francisco-Oakland-Hayward, CA",
    "method": "GET",
    "page": "Home",
    "registration": 1540919166796.0,
    "sessionId": 38,
    "song": null,
    "status": 200,
    "ts": 1541105830796,
    "userAgent": "\"Mozilla\/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit\/537.36 (KHTML, like Gecko) Chrome\/36.0.1985.143 Safari\/537.36\"",
    "userId": "39"
}
....
{
...
}
....
```

We will use the `log_json_path.json` JSONPath manifest to inform Redshift on how to import the JSON data files with a `COPY` from S3 command.

```json
{
    "jsonpaths": [
        "$['artist']",
        "$['auth']",
        "$['firstName']",
        "$['gender']",
        "$['itemInSession']",
        "$['lastName']",
        "$['length']",
        "$['level']",
        "$['location']",
        "$['method']",
        "$['page']",
        "$['registration']",
        "$['sessionId']",
        "$['song']",
        "$['status']",
        "$['ts']",
        "$['userAgent']",
        "$['userId']"
    ]
}
```

Notes (resources):
- [COPY examples in Redshift](https://docs.aws.amazon.com/redshift/latest/dg/r_COPY_command_examples.html#copy-from-json-examples-using-jsonpaths)
- [COPY from JSON format in Redshift](https://docs.aws.amazon.com/redshift/latest/dg/copy-usage_notes-copy-from-json.html)
- [Load from JSON data using a JSONPaths file in Redshift](
https://docs.aws.amazon.com/redshift/latest/dg/r_COPY_command_examples.html#copy-from-json-examples-using-jsonpaths)

## Data model specificities

You can learn more about Redshift specificities here:

- [Redshift data types](https://hevodata.com/blog/amazon-redshift-data-types/
). Even if Redshift is based on Postgres, some Redshift data types may differ from [Postgres data types](https://www.postgresql.org/docs/9.1/datatype-numeric.html
).
- [Converting Redshift epochs and timestamps](
https://www.fernandomc.com/posts/redshift-epochs-and-timestamps/)
- [Defining constraints in Redshift](https://docs.aws.amazon.com/redshift/latest/dg/t_Defining_constraints.html). As per the documentation, "uniqueness, primary key, and foreign key constraints are informational only; they are not enforced by Amazon Redshift.". Primary keys and not null constraints are recommended only when you can guarantee their validity.
- [Unique autogenerated values with IDENTITY for columns candidates to auto increments](https://docs.aws.amazon.com/redshift/latest/dg/r_CREATE_TABLE_NEW.html)

A quick refresher on the main data types in play in this project:

- Numeric data types and their ranges:

```console
Name      Size     Minimum               Maximum
smallint  2 bytes  -32768                +32767
integer   4 bytes  -2147483648           +2147483647
bigint    8 bytes  -9223372036854775808  +9223372036854775807
```

- Choice between BIGINT AND INT for epoch to date conversions:

```console
Name      Size     Minimum Date      Maximum Date
smallint  2 bytes  1969-12-31        1970-01-01
integer   4 bytes  1901-12-13        2038-01-18
bigint    8 bytes  -292275055-05-16  292278994-08-17
