import csv
from flask import Flask, render_template, request, flash
import time
import numpy as np
import tensorflow as tf
from flask_mail import Mail, Message  # Import Mail and Message
from email_utils import send_email
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'AppAnomalyykey'
# Flask-Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

mail = Mail(app)  # Initialize Mail with the app

# Feature parameters (min and max for each feature)
feature_params = {
    'SourceIP': {'min': 0, 'max': 1000000000},
    'DestinationIP': {'min': 0, 'max': 1000000000},
    'SourcePort': {'min': 0, 'max': 65535},
    'Protocol': {'min': 0, 'max': 10},
    'BytesSent': {'min': 0, 'max': 10000},
    'BytesReceived': {'min': 0, 'max': 10000},
    'PacketsSent': {'min': 0, 'max': 100},
    'PacketsReceived': {'min': 0, 'max': 100},
    'Duration': {'min': 0, 'max': 100}
}


def min_max_normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)


@app.before_request
def before_request():
    # Record the start time before handling the request to calculate duration
    request.start_time = time.time()


@app.route('/')
def hello():
    # Get IP Source (Client IP)
    ip_source = request.remote_addr

    # Get Port Source (Client Port)
    port_source = request.environ.get('REMOTE_PORT')

    # Placeholder values for other metrics
    # In a real-world scenario, these would be collected from the application/server logs or network data
    ip_destination = request.host  # Server IP
    packets_sent = 100  # Example value
    packets_received = 150  # Example value
    bytes_sent = 1024  # Example value in bytes
    duration = time.time() - request.start_time  # Example duration calculation

    # Prepare the data row for normalization
    data_row = {
        'SourceIP': int(ip_source.replace('.', '')),
        'DestinationIP': int(port_source),
        'SourcePort': 80,  # Assume HTTP port, replace with actual port if known
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

    # Save the normalized data row to CSV
    csv_filename = 'normalized_data.csv'
    with open(csv_filename, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(normalized_data_row.keys())  # Write header
        writer.writerow(normalized_data_row.values())  # Write data

    # Load the saved model
    model_path = 'models/model_syn_cnn_retrained.keras'
    try:
        model = tf.keras.models.load_model(model_path)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        return f"Error loading model: {e}"

    # Prepare the data for prediction
    row_data = np.array(list(normalized_data_row.values())).reshape(1, -1)

    # Reshape the data to match the input shape of the model
    X_input = row_data.reshape(1, 9, 1)

    # Perform prediction
    try:
        prediction = model.predict(X_input)
        anomaly_threshold = 0.5
        is_anomaly = prediction > anomaly_threshold

        prediction_result = "Anomaly" if is_anomaly else "Normal"
    except Exception as e:
        print(f"Error during prediction: {e}")
        return f"Error during prediction: {e}"

    # Send Email
    subject = f"Testing Anomaly on {ip_destination}"
    recipient = "wisdomraphael9@gmail.com"
    body = f"""
<html>
    <body>
        <h2><strong>The network traffic is classified as: {prediction_result}</strong></h2>
        <p>and the prediction confidence is {prediction[0][0]}</p>
    </body>
</html>
"""
    send_email(mail, subject, recipient, body)

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
        'prediction_result': prediction_result,
        'prediction': prediction
    }

    return render_template('landing.html', **context)


if __name__ == '__main__':
    app.run(debug=True)
