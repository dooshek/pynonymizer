
# PyNonimizer - PostgreSQL Database Anonymizer

This Python script is designed to anonymize specified fields in a PostgreSQL database using Faker to generate fake data. It is particularly useful in environments where sensitive data needs to be masked before sharing databases or datasets with third-party developers or for testing purposes.

## Features

- Anonymize specified fields across multiple tables.
- Supports unique and primary key constraints for ensuring data integrity.
- Allows ignoring specific records from being anonymized.
- Configurable through a YAML definitions file for specifying which tables and fields to anonymize.
- Ability to specify Faker locales for generating localized data.
- Command-line arguments for database connection and configuration.

## Prerequisites

To run this script, you need:

- Python 3.x
- PostgreSQL database
- Python packages: `psycopg2`, `faker`, `pyyaml`

Ensure these are installed before proceeding. You can install the required Python packages using:

```sh
pip install -r requirements.txt
```

## Usage
Prepare YAML Configuration Files:

`defs.yaml`: Define the tables and fields you want to anonymize, along with the Faker methods to use for generating the fake data. Optionally, configure [Faker locales](https://faker.readthedocs.io/en/master/locales.html).

`ignores.yaml`: Specify any record IDs you wish to ignore and not anonymize.

## Run the Script:

Use the following command to run the script:

```bash
python anonymize.py --host <db_host> --port <db_port> --user <db_user> --name <db_name> --password <db_password> [--defs defs.yaml] [--ignores ignores.yaml] [--log-level info]
```

Replace <db_host>, <db_port>, <db_user>, <db_name>, and <db_password> with your database connection details.

## Configuration Example

`defs.yaml`
```yaml
faker:
  locales: ["en_US"]
tables:
  users:
    email: "email"
    name: "name"
```

`ignores.yaml`

```yaml
ignore_ids:
  - 1
  - 2
```

## Command-line Arguments

`--host`: Database host.

`--port`: Database port.

`--user`: Database user.

`--name`: Database name.

`--password`: Database password.

`--defs`: Path to the table definitions YAML file. Default is defs.yaml.

`--ignores`: Path to the ignore list YAML file. Default is ignores.yaml.

`--log-level`: Logging level (debug, info, warning, error, critical). Default is info.

## Final note
Ensure that the YAML configuration files accurately reflect your database schema.

__Always create a backup of your database before running this script!__

## License
This project is open source and available under the MIT License.

