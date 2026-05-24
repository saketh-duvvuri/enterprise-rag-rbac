import psycopg2
try:
    conn = psycopg2.connect('postgresql://postgres:mysecretpassword@localhost:5432/ragdb')
    print('✅ Success: Python is connected to Docker!')
    conn.close()
except Exception as e:
    print(f'❌ Failed: {e}')
