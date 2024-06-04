from flask import Flask, request, jsonify
from azure.data.tables import TableServiceClient
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
from flask_cors import CORS
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for specific origin and methods

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
    row_key = request.args.get('row_key', None)  # Get row_key from query parameters if provided

    # Construct the query
    query = f"TS ge '{start_date}' and TS lt '{end_date}'"
    if row_key:
        query += f" and RowKey eq '{row_key}'"

    entities = table_client.query_entities(query_filter=query)
    data = []
    for e in entities:
        row_key = e.get("RowKey")
        if row_key:
            data.append({
                "Timestamp": e.get("TS"),
                "Description": e.get("Description"),
                "Weevil_number": e.get("Weevil_number"),
                "ImageUrl": e.get("ImageUrl"),
                "rowKey": row_key
            })
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

@app.route('/api/update_peaweevil', methods=['POST'])
def update_peaweevil():
    data = request.get_json()
    print('Received data:', data)
    row_key = data.get('rowKey')  # 更正字段名称
    new_number = data.get('newWeevilNumber')  # 更正字段名称

    entity = table_client.get_entity(partition_key="ImageDescription", row_key=row_key)
    entity['Weevil_number'] = new_number
    table_client.update_entity(entity)
    return jsonify({"message": "Peaweevil number updated successfully"}), 200

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    print('Received data:', data)
    client = OpenAI(
    # This is the default and can be omitted
        api_key=os.environ.get("OPENAI_API_KEY"),
        base_url="https://openai.ianchen.io/v1",
    )

    messages = data.get('messages', [])
    chat_completion = client.chat.completions.create(
        messages=messages,
        model="gpt-3.5-turbo",
    )
    response = {}
    response["message"] = chat_completion.choices[0].message.content
    return jsonify(response)

if __name__ == '__main__':
    app.run(debug=True)