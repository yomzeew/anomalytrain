import csv
import time
from flask import Flask, render_template, request
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler

app = Flask(__name__)

# Load the trained model
model = tf.keras.models.load_model('models/model_syn_cnn_retrained.keras')

# Define feature parameters for normalization
feature_params = {
    'SourceIP': {'min': 0, 'max': 1000000000},
    'SourcePort': {'min': 0, 'max': 65535},
    'DestinationPort': {'min': 0, 'max': 65535},
    'Protocol': {'min': 0, 'max': 10},
    'BytesSent': {'min': 0, 'max': 10000},
    'BytesReceived': {'min': 0, 'max': 10000},
    'PacketsSent': {'min': 0, 'max': 100},
    'PacketsReceived': {'min': 0, 'max': 100},
    'Duration': {'min': 0, 'max': 100}
}
[ 'DestinationIP', 'SourcePort', 'DestinationPort',
       'Protocol', 'BytesSent', 'BytesReceived', 'PacketsSent',
       'PacketsReceived', 'Duration',]
def min_max_normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)

@app.before_request
def before_request():
    # Record the start time before handling the request to calculate duration
    request.start_time = time.time()

@app.route('/')
def index():
    # Get IP Source (Client IP)
    ip_source = request.remote_addr

    # Get Port Source (Client Port)
    port_source = request.environ.get('REMOTE_PORT')

    # Placeholder values for other metrics
    ip_destination = request.host  # Server IP
    packets_sent = 100  # Example value
    packets_received = 150  # Example value
    bytes_sent = 1024  # Example value in bytes
    duration = time.time() - request.start_time  # Example duration calculation

    # Prepare the data row for normalization
    data_row = {
        'DestinationPort': 100000,
        'SourceIP': int(ip_source.replace('.', '')),
        'SourcePort': int(port_source),
        'DestinationPort': 80,  # Assume HTTP port, replace with actual port if known
        'Protocol': 6,  # Assuming TCP for this example
        'BytesSent': bytes_sent,
        'BytesReceived': 2048,  # Placeholder value for bytes received
        'PacketsSent': packets_sent,
        'PacketsReceived': packets_received,
        'Duration': duration
    }

    # Normalize each feature in the data row
    normalized_data_row = {key: min_max_normalize(data_row[key],
                                                  feature_params[key]['min'],
                                                  feature_params[key]['max'])
                           for key in data_row}

    # Convert normalized data to DataFrame and scale
    df = pd.DataFrame([normalized_data_row])
    
    # Ensure you use the same scaler used during training if saved
    scaler = MinMaxScaler()
    df_scaled = scaler.fit_transform(df)  # Adjust if you saved and loaded the scaler

    # Reshape data to match model input shape
    num_features = df_scaled.shape[1]
    sequence_length = 1  # Adjust according to your model's expected input
    X_input = df_scaled.reshape(1, 10, 1)

    # Perform prediction
    try:
        prediction = model.predict(X_input)
        anomaly_threshold = 0.5
        is_anomaly = prediction[0] > anomaly_threshold
    except Exception as e:
        is_anomaly = None
        print(f"Error during prediction: {e}")

    # Save the normalized data to CSV
    csv_filename = 'normalized_data.csv'
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(normalized_data_row.keys())  # Write header
        writer.writerow(normalized_data_row.values())  # Write data

    # Prepare the data to send to the template
    context = {
        'ip_source': ip_source,
        'ip_destination': ip_destination,
        'port_source': port_source,
        'packets_sent': packets_sent,
        'packets_received': packets_received,
        'bytes_sent': bytes_sent,
        'duration': duration,
        'normalized_data_row': normalized_data_row,
        'is_anomaly': is_anomaly
    }

    return render_template('index.html', **context)

if __name__ == '__main__':
    app.run(debug=True)
