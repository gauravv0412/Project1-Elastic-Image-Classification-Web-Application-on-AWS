from flask import Flask, request
import boto3
import json
import io
from PIL import Image
import os

app = Flask(__name__)
s3 = boto3.client('s3')
sqs = boto3.resource('sqs', region_name='us-east-1')

# Request and Response Queue
request_queue = sqs.get_queue_by_name(QueueName='RequestQueue')
response_queue = sqs.get_queue_by_name(QueueName='ResponseQueue')

# Input and Output S3 Buckets
INPUT_BUCKET_NAME = "inputapptierbucket"
OUTPUT_BUCKET_NAME = "outputapptierbucket"

# Startup Page
@app.route('/')
def home():
    try:
        os.remove('logs_file.txt')
        os.remove('results.txt')
    except:
        pass
    return "App Started"

# Main functionality of Web-Tier
@app.route('/upload-image', methods=['POST'])
def upload_image():

  file = request.files['myfile']
  filename = file.filename
  file_contents = file.read()
  image = Image.open(io.BytesIO(file_contents))
  jpeg_image = io.BytesIO()
  image.save(jpeg_image, 'JPEG')
  jpeg_data = jpeg_image.getvalue()

  s3.put_object(Body=jpeg_data, Bucket=INPUT_BUCKET_NAME, Key=filename)

  message = {'filename': filename}
  request_queue.send_message(MessageBody=json.dumps(message))
  # Check if the message received contains the key we are waiting for
  while True:
    try:
      with open('results.txt', 'r') as fr:
        fr.seek(0)
        lines = fr.readlines()
        for line in lines:
          if filename in line:
            with open('logs_file.txt', 'a+') as fa:
              fa.seek(0)
              x = fa.readlines()
              cnt = 1 if x == [] else int(x[-1].split(' ')[0]) + 1
              fa.write(str(cnt) + ' '+ line)
            return line
    except:
      pass

    messages = response_queue.receive_messages(MaxNumberOfMessages=10, WaitTimeSeconds=3)
#    print(len(messages))
    for message in messages:
      msg = json.loads(str(message.body))
      image_name = list(msg.keys())[0]
      s3_response = s3.get_object(Bucket = OUTPUT_BUCKET_NAME, Key = image_name[:-5])
      file_stream = s3_response['Body']
      txt = str(file_stream.read())
      image_name, ans = txt.split(',')
      image_name = image_name[3:]
      ans = ans[:-4]
      with open('results.txt', 'a+') as fa:
        fa.write(image_name + ".JPEG : " + ans + '\n')
      message.delete()

if __name__ == "__main__":
    app.run(threaded = True)
