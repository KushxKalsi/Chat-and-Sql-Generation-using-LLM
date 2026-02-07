#!/usr/bin/env python3
"""
Database API Server for Raspberry Pi
This creates an HTTP API that your Flask app can call to query the database
Run this on your Raspberry Pi: python3 db-api-server.py
Then expose it via cloudflared: api.kushkalsi.in -> http://127.0.0.1:5001
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import pymysql
import json

app = Flask(__name__)
CORS(app)  # Allow requests from your Windows PC

DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': 'kushkalsilav',
    'database': 'test',
    'charset': 'utf8mb4',
    'cursorclass': pymysql.cursors.DictCursor
}

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

@app.route('/query', methods=['POST'])
def execute_query():
    """Execute a SQL query and return results"""
    data = request.json
    sql_query = data.get('query', '')
    
    if not sql_query:
        return jsonify({'error': 'No query provided'}), 400
    
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            cursor.execute(sql_query)
            results = cursor.fetchall()
        connection.close()
        
        return jsonify({
            'success': True,
            'data': results,
            'row_count': len(results)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/schema', methods=['GET'])
def get_schema():
    """Get database schema"""
    try:
        connection = pymysql.connect(**DB_CONFIG)
        with connection.cursor() as cursor:
            # Get all tables
            cursor.execute("SHOW TABLES")
            tables = [list(row.values())[0] for row in cursor.fetchall()]
            
            schema_info = {}
            for table in tables:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                schema_info[table] = columns
        
        connection.close()
        
        return jsonify({
            'success': True,
            'schema': schema_info
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    print("Starting Database API Server on port 5001...")
    print("Expose this via cloudflared: api.kushkalsi.in -> http://127.0.0.1:5001")
    app.run(host='0.0.0.0', port=5001, debug=True)
