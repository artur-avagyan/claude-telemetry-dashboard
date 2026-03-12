import json
import sqlite3

import pandas as pd
from tqdm import tqdm

JSONL_PATH = "./data/output/telemetry_logs.jsonl"
EMPLOYEES_PATH = "./data/output/employees.csv"
DB_PATH = "./data/telemetry.db"


def load_raw_data():
    # Step 1: Open the JSONL file and parse each line as a JSON object
    with open(JSONL_PATH, "r") as f:
        data = [json.loads(line) for line in f if line.strip()]
    return data


def parse_events(data):
    rows = []
    for batch in tqdm(data, desc="Parsing events"):
        for event in batch["logEvents"]:
            # Step 2: Parse the nested message JSON string into a dict
            row = json.loads(event["message"])
            # Step 3: Convert the millisecond timestamp to a readable datetime
            row["timestamp"] = pd.to_datetime(event["timestamp"], unit="ms")
            # Step 4: Keep the log event ID for traceability
            row["log_id"] = event["id"]
            rows.append(row)
    # Step 5: Flatten all nested dicts into a single wide DataFrame
    df = pd.json_normalize(rows)
    # Step 6: Convert the ISO 8601 event timestamp string to datetime dtype
    df["attributes.event.timestamp"] = pd.to_datetime(df["attributes.event.timestamp"])
    return df


def build_users(df):
    # Step 7: Load employee metadata (name, level, location, practice) from CSV
    employees = pd.read_csv(EMPLOYEES_PATH)
    # Step 8: Get one unique row per user from telemetry
    users = df[["attributes.user.id", "attributes.user.email"]].drop_duplicates(
        subset="attributes.user.id"
    )
    # Step 9: Enrich user rows with employee metadata via email join
    users = users.merge(employees, left_on="attributes.user.email", right_on="email", how="left")
    # Step 10: Rename columns to clean names and drop the duplicate email column
    users = users.rename(columns={
        "attributes.user.id": "user_id",
        "attributes.user.email": "user_email",
        "full_name": "user_full_name",
        "practice": "user_practice",
        "level": "user_level",
        "location": "user_location",
    }).drop(columns=["email"])
    return users


def build_sessions(df):
    # Step 11: Extract one row per unique session with session-level metadata
    return df[[
        "attributes.session.id", "attributes.terminal.type",
        "attributes.user.id", "attributes.organization.id",
        "scope.version", "resource.user.serial",
    ]].drop_duplicates().reset_index(drop=True)


def build_resources(df):
    # Step 12: Extract machine/environment info (OS, host, arch) per session
    resource_cols = ["attributes.session.id", "attributes.user.id"] + [
        col for col in df.columns if "resource" in col
    ]
    return df[resource_cols].drop_duplicates().reset_index(drop=True)


def build_events(df):
    # Step 13: Build the base events table — one row per log entry with shared fields
    return df[[
        "log_id", "attributes.session.id", "attributes.user.id",
        "attributes.event.timestamp", "attributes.event.name", "scope.version",
    ]].drop_duplicates().reset_index(drop=True)


def build_user_prompts(df):
    # Step 14: Filter only user_prompt events and keep prompt-specific fields
    return df[df["body"] == "claude_code.user_prompt"][[
        "log_id", "attributes.prompt_length",
    ]].reset_index(drop=True)


def build_api_requests(df):
    # Step 15: Filter only api_request events and keep model/token/cost fields
    return df[df["body"] == "claude_code.api_request"][[
        "log_id", "attributes.model", "attributes.input_tokens",
        "attributes.output_tokens", "attributes.cache_read_tokens",
        "attributes.cache_creation_tokens", "attributes.cost_usd", "attributes.duration_ms",
    ]].reset_index(drop=True)


def build_tool_decisions(df):
    # Step 16: Filter only tool_decision events (accept/reject per tool)
    return df[df["body"] == "claude_code.tool_decision"][[
        "log_id", "attributes.tool_name", "attributes.source", "attributes.decision",
    ]].reset_index(drop=True)


def build_tool_results(df):
    # Step 17: Filter only tool_result events (execution outcome per tool)
    return df[df["body"] == "claude_code.tool_result"][[
        "log_id", "attributes.tool_name", "attributes.success",
        "attributes.duration_ms", "attributes.decision_source",
        "attributes.decision_type", "attributes.tool_result_size_bytes",
    ]].reset_index(drop=True)


def build_api_errors(df):
    # Step 18: Filter only api_error events (failed API calls with error details)
    return df[df["body"] == "claude_code.api_error"][[
        "log_id", "attributes.model", "attributes.error",
        "attributes.status_code", "attributes.attempt", "attributes.duration_ms",
    ]].reset_index(drop=True)


def save_to_db(tables: dict):
    # Step 19: Connect to (or create) the SQLite database file
    conn = sqlite3.connect(DB_PATH)
    for table_name, table_df in tables.items():
        # Step 20: Write each DataFrame as a table, replacing it if it already exists
        table_df.to_sql(table_name, conn, if_exists="replace", index=False)
        print(f"  Saved {len(table_df):,} rows → {table_name}")
    # Step 21: Close the database connection
    conn.close()


def main():
    # Step 1: Load raw JSONL batches from disk
    print("Loading raw data...")
    data = load_raw_data()

    # Step 2: Parse and flatten all log events into a single DataFrame
    print("Parsing events...")
    df = parse_events(data)

    # Step 3: Build each normalized table from the flat DataFrame
    print("Building tables...")
    tables = {
        "users":          build_users(df),          # unique users + employee metadata
        "sessions":       build_sessions(df),        # unique sessions per user
        "resources":      build_resources(df),       # machine/OS info per session
        "events":         build_events(df),          # base table for all events
        "user_prompts":   build_user_prompts(df),    # prompt-specific fields
        "api_requests":   build_api_requests(df),    # model/token/cost fields
        "tool_decisions": build_tool_decisions(df),  # tool accept/reject decisions
        "tool_results":   build_tool_results(df),    # tool execution outcomes
        "api_errors":     build_api_errors(df),      # failed API call details
    }

    # Step 4: Write all tables to the SQLite database
    print("Saving to SQLite...")
    save_to_db(tables)
    print("Done!")


if __name__ == "__main__":
    main()
