// Use if Navigator fails: Home -> Get data -> Blank query -> Advanced editor
// Paste ONE block at a time, set credentials when prompted (Database / SAJY + password)

// --- gold_daily_summary ---
let
    Source = Snowflake.Databases(
        "QOGRAXH-UQ68486.snowflakecomputing.com",
        "COMPUTE_WH",
        [Role = "ACCOUNTADMIN"]
    ),
    DB = Source{[Name = "spotify", Kind = "Database"]}[Data],
    Schema = DB{[Name = "gold", Kind = "Schema"]}[Data],
    View = Schema{[Name = "gold_daily_summary", Kind = "View"]}[Data]
in
    View

// --- silver_tracks (separate blank query) ---
let
    Source = Snowflake.Databases(
        "QOGRAXH-UQ68486.snowflakecomputing.com",
        "COMPUTE_WH",
        [Role = "ACCOUNTADMIN"]
    ),
    DB = Source{[Name = "spotify", Kind = "Database"]}[Data],
    Schema = DB{[Name = "silver", Kind = "Schema"]}[Data],
    Table = Schema{[Name = "silver_tracks", Kind = "Table"]}[Data]
in
    Table
