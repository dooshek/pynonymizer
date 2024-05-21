#!/bin/env python3
import argparse
from enum import unique
import logging
import time
import faker
import psycopg2.extras
import yaml
import psycopg2
from psycopg2 import extras
from sys import exit
from faker import Faker
from psycopg2.errors import UniqueViolation
from concurrent.futures import ThreadPoolExecutor

# Setup argument parser
parser = argparse.ArgumentParser()
parser.add_argument("--host", required=True)
parser.add_argument("--port", required=True)
parser.add_argument("--user", required=True)
parser.add_argument("--name", required=True)
parser.add_argument("--password", required=True)
parser.add_argument("--defs", default="defs.yaml")
parser.add_argument("--ignores", default="ignores.yaml")
parser.add_argument("--log-level", default="info", choices=["debug", "info", "warning", "error", "critical"])
parser.add_argument("--threads", type=int, default=1)

args = parser.parse_args()

# Setup logging
numeric_level = getattr(logging, args.log_level.upper(), None)
logging.basicConfig(level=numeric_level)

# Read table definitions and ignored IDs
with open(args.defs, 'r') as file:
    defs = yaml.safe_load(file)

with open(args.ignores, 'r') as file:
    ignored_ids = yaml.safe_load(file)["ignore_ids"]

# Initialize Faker
locales = defs.get('faker', {}).get('locales', ['en_US'])
fake = Faker(locales)

def process_table(table, fields, ignored_ids):
    conn = psycopg2.connect(
        dbname=args.name,
        user=args.user,
        password=args.password,
        host=args.host,
        port=args.port
    )
    conn.autocommit = False
    cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
    cursor_select = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    def get_unique_constraints(table_name):
        cursor.execute(f"""
            SELECT a.attname
            FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                AND a.attnum = ANY(i.indkey)
            WHERE  i.indrelid = '{table_name}'::regclass
            AND    i.indisunique;
        """)
        results = cursor.fetchall()
        if results is None:
            return None
        return [result[0] for result in results]
        
    def get_primary_key(table_name):
        cursor.execute(f"""
            SELECT a.attname
            FROM   pg_index i
            JOIN   pg_attribute a ON a.attrelid = i.indrelid
                                AND a.attnum = ANY(i.indkey)
            WHERE  i.indrelid = '{table_name}'::regclass
            AND    i.indisprimary;
        """)
        result = cursor.fetchone()
        if result is None:
            return None
        return result[0]

    def update_record(table, pk, pk_value, updated_values: dict):
        try:
            updates = [f"{field} = %s" for field in updated_values.keys()]
            values = list(updated_values.values())
            values.append(pk_value)
            updates_str = ', '.join(updates)
            cursor.execute(f"UPDATE {table} SET {updates_str} WHERE {pk} = %s", values)
            return True
        except UniqueViolation as e:
            logging.warning(f"Duplicate key value violation. Regenerating...")
            return False
        
    pk = get_primary_key(table)
    unique_fields = get_unique_constraints(table)
    
    if pk is None:
        logging.warning(f"Skipping table {table} due to missing primary key.")
        cursor.close()
        conn.close()
        return

    cursor.execute(f"SELECT COUNT(*) FROM {table}")
    total_count = cursor.fetchone()[0]
    logging.info(f"Processing table {table} with {total_count} records...")
    table_start_time = time.time()
    updated_count = 0
    faker_cache = {}
    
    cursor_select.execute(f"SELECT {pk}, {', '.join(fields.keys())} FROM {table}")
    while True:
        try:
            record = cursor_select.fetchone()
            if record is None:
                break
        except psycopg2.ProgrammingError:
            break
            
        if record[pk] in ignored_ids:
            logging.warning(f"Skipping update for {table} with {pk} = {record[pk]} due to ignore list.")
            continue

        updated_values = {}
        for field, faker_method in fields.items():
            if not hasattr(fake, faker_method):
                logging.error(f'Faker does not support the method: {faker_method}')
                exit(1)
            
            value = getattr(fake, faker_method)()

            # Field is unique, we need to check if the value has already been used and regenerate if necessary
            if field in unique_fields:
                while (value in faker_cache):
                    value = getattr(fake, faker_method)()

            faker_cache[value] = True
            updated_values[field] = value

        try:
            update_record(table, pk, record[pk], updated_values), 
            updated_count += 1
        except psycopg2.Error as e:
            logging.error(f"Error updating record: {e}")
            conn.rollback()
                                            
    # Commit the transaction
    conn.commit()
    logging.info(f"Processed {updated_count} records in {table}, time taken: {time.time() - table_start_time:.2f} seconds")
    cursor.close()
    conn.close()

def main():
    start_time = time.time()

    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        for table, fields in defs["tables"].items():
            executor.submit(process_table, table, fields, ignored_ids)

    logging.info(f"Total time for script execution: {time.time() - start_time:.2f} seconds")
    
if __name__ == "__main__":
    main()
