from scripts import clickhouse_http

with open("infra/clickhouse/sql/004_tick_quality_checks.sql", "r") as f:
    sql_content = f.read()

statements = [s.strip() for s in sql_content.split(";") if s.strip()]

for i, stmt in enumerate(statements):
    print(f"Executing statement {i+1}/{len(statements)}...")
    clickhouse_http.execute(stmt)
print("All quality checks applied.")
