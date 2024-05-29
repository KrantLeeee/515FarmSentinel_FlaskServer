from flask import Flask, request, jsonify
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from flask_cors import CORS
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000/dashboard"}})  # Enable CORS for specific origin

connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
table_service = TableServiceClient.from_connection_string(conn_str=connection_string)
table_client = table_service.get_table_client(table_name="DeviceTest01")
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client("assets")

@app.route('/')
def home():
    return "Welcome to the Flask API Server!"

@app.route('/api/data', methods=['GET'])
def get_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    query = f"TS ge '{start_date}' and TS lt '{end_date}'"
    entities = table_client.query_entities(query_filter=query)
    data = [{"Timestamp": e["TS"], "Description": e["Description"], "Weevil_number": e["Weevil_number"], "ImageUrl": e["ImageUrl"]} for e in entities]
    return jsonify(data)

@app.route('/api/capture', methods=['POST'])
def capture_now():
    blob_name = "trigger.txt"
    blob_content = "capture now"

    try:
        blob_client = container_client.get_blob_client(blob_name)
        blob_client.upload_blob(blob_content, overwrite=True)
        return jsonify({"message": "Capture triggered"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
