from flask import Flask, render_template, request
import boto3
import json
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
s3 = boto3.client('s3')
sqs = boto3.resource('sqs', region_name='us-east-1')
queue = sqs.get_queue_by_name(QueueName='StdQueue1')
BUCKET_NAME = "inputapptierbucket"

@app.route('/')
def home():
    return "App Started"

@app.route('/upload-image', methods=['post'])
def upload_image():
    file = request.files['image']
    filename = file.filename
    s3.upload_file(
                    Bucket = BUCKET_NAME,
                    Filename=filename,
                    Key = filename
                )
    message = {'filename': filename}
    queue.send_message(MessageBody=json.dumps(message))
    return f'{filename} uploaded!\n'

if __name__ == "__main__":
    app.run(debug=True)
