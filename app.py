from flask import Flask, request, jsonify
from azure.data.tables import TableServiceClient
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
table_client = table_service.get_table_client(table_name="DeviceTest01")

@app.route('/')
def home():
    return "Welcome to the Flask API Server!"

@app.route('/api/data', methods=['GET'])
def get_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query = f"TS ge '{start_date}' and TS lt '{end_date}'"
    entities = table_client.query_entities(query_filter=query)
    data = [{"Timestamp": e["TS"],"Description": e["Description"], "Weevil_number": e["Weevil_number"]} for e in entities]
    return jsonify(data)

if __name__ == '__main__':
    app.run(debug=True)
