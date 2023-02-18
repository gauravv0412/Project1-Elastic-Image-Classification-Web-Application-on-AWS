from flask import Flask, request
import boto3
import json
import io
from PIL import Image

app = Flask(__name__)
s3 = boto3.client('s3')
sqs = boto3.resource('sqs', region_name='us-east-1')
request_queue = sqs.get_queue_by_name(QueueName='RequestQueue')
response_queue = sqs.get_queue_by_name(QueueName='ResponseQueue')
BUCKET_NAME = "inputapptierbucket"

@app.route('/')
def home():
    return "App Started"

@app.route('/upload-image', methods=['POST'])
def upload_image():

    file = request.files['myfile']
    filename = file.filename
    file_contents = file.read()

    image = Image.open(io.BytesIO(file_contents))
    jpeg_image = io.BytesIO()
    image.save(jpeg_image, 'JPEG')
    jpeg_data = jpeg_image.getvalue()

    s3.put_object(Body=jpeg_data, Bucket=BUCKET_NAME, Key=filename)

    message = {'filename': filename}
    request_queue.send_message(MessageBody=json.dumps(message))

    # Check if the message received contains the key we are waiting for
    while True:
        # Receive messages from the queue
        messages = response_queue.receive_messages(MaxNumberOfMessages=10)
        

        # Check if the message received contains the key we are waiting for
        for message in messages:
            # print(f'checking for {filename} : {message.body}')
            if filename in message.body:
                # msg = message.body['filename']
                msg = json.loads(message.body)
                k = message.delete()
                # print(f"On Deleting : {k}")
                return f"{msg[filename]}"

if __name__ == "__main__":
    app.run(host = '0.0.0.0', port = 5000)
