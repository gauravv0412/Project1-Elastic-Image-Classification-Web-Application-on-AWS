
import os
import ast
import yaml
import boto3
from PIL import Image

with open('../settings.yaml') as f:
    settings = yaml.safe_load(f)

s3 = boto3.client('s3', aws_access_key_id=settings['aws_access_key_id'], 
                        aws_secret_access_key=settings['aws_secret_access_key'])
sqs = boto3.client('sqs', region_name='us-east-1', 
                        aws_access_key_id=settings['aws_access_key_id'], 
                        aws_secret_access_key=settings['aws_secret_access_key'])

INPUT_BUCKET_NAME = settings["input_bucket_name"]
OUTPUT_BUCKET_NAME = settings["output_bucket_name"]
REQUEST_QUEUE_URL = settings['sqs_request_queue']
RESPONSE_QUEUE_URL = settings['sqs_response_queue']


while(True):
    # Receive message from SQS queue
    request = sqs.receive_message(
        QueueUrl=REQUEST_QUEUE_URL,
        AttributeNames=[
            'SentTimestamp'
        ],
        MaxNumberOfMessages=1,
        MessageAttributeNames=[
            'All'
        ],
        VisibilityTimeout=10,
        WaitTimeSeconds=0
    )

    receiptHandle = request['Messages'][0]['ReceiptHandle']
    sqs.delete_message(QueueUrl=REQUEST_QUEUE_URL, ReceiptHandle=receiptHandle)

    filename = ast.literal_eval(request['Messages'][0]['Body'])['filename']
    s3_response = s3.get_object(Bucket=INPUT_BUCKET_NAME, Key=filename)
    file_stream = s3_response['Body']
    file = Image.open(file_stream)
    filepath = '../classifier/'+filename
    file.save(filepath)

    output = os.system(f"python3 image_classification.py {filepath}")

    # output='test-image.jpg,pedestal'
    output = output.split(',')
    output_key = output[0].split('.')[0]
    output_value = (output_key,output[1])

    s3.put_object(Body=output_value, Bucket=OUTPUT_BUCKET_NAME, Key=output_key)

    # Send message to SQS response queue
    response = sqs.send_message(
        QueueUrl=RESPONSE_QUEUE_URL,
        MessageBody= output_value
    )
