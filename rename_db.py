import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres:3513@localhost:5432/postgres")
    conn.autocommit = True
    cur = conn.cursor()
    
    # Terminate active connections to CareEquity
    cur.execute("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'CareEquity';")
    print("Terminated existing active connections.")
    
    # Rename database
    cur.execute('ALTER DATABASE "CareEquity" RENAME TO careequity;')
    print("Successfully renamed database 'CareEquity' to 'careequity'!")

    cur.close()
    conn.close()
except Exception as e:
    print("Error during database rename:", e)
