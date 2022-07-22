"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: MIT-0
Permission is hereby granted, free of charge, to any person obtaining a copy of this
software and associated documentation files (the "Software"), to deal in the Software
without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
from distutils.command.config import config
import os
import boto3
from datetime import datetime
import json
import csv
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

today = datetime.now().strftime("%Y-%m-%d")  # Currnent day
filename = f'/tmp/changed_resources-{today}.csv'  # CSV report filename
AGGREGATOR_NAME = os.environ['AGGREGATOR_NAME']  # AWS Config Aggregator name
SENDER = os.environ['SENDER']  # SES Sender address
RECIPIENT = os.environ['RECIPIENT']  # SES Recipient address


# Generate the resource link to AWS Console UI
def get_link(aws_region, resource_id, resource_type):
    return f'https://{aws_region}.console.aws.amazon.com/config/home?region={aws_region}#/resources/timeline?resourceId={resource_id}&resourceType={resource_type}'


# Generate the CSV Report
def create_report(AGGREGATOR_NAME, today, filename):
    client = boto3.client('config')
    response = client.select_aggregate_resource_config(
        Expression=f"SELECT * WHERE configurationItemCaptureTime LIKE '{today}%'",
        ConfigurationAggregatorName=AGGREGATOR_NAME
    )
    changed_resources = response["Results"]
    json_list = [json.loads(line) for line in changed_resources]
    # Transform the JSON response to CSV file
    for resource in json_list:
        aws_region = resource['awsRegion']
        resource_id = resource['resourceId']
        resource_type = resource['resourceType']
        resource['Link'] = get_link(aws_region, resource_id, resource_type)
        print(resource)
    all_fields = set()
    for item in json_list:
        all_fields.update(item.keys())
    # Save the report file
    with open(filename, 'w', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=list(all_fields))
        writer.writeheader()
        writer.writerows(json_list)
    print("Report generated " + filename)


def send_email(today, SENDER, RECIPIENT, filename):
    # The subject line for the email.
    SUBJECT = f"AWS Config changes report {today}"
    ATTACHMENT = filename
    BODY_TEXT = "Hello,\r\nPlease see the attached file which includes the changes made during the last day."
    ses = boto3.client('ses')

    # The HTML body of the email.
    BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <p>Hello, please see the attached file which includes the changes made during the last day.</p>
    </body>
    </html>
    """
    CHARSET = "utf-8"
    msg = MIMEMultipart('mixed')
    msg['Subject'] = SUBJECT
    msg['From'] = SENDER
    msg['To'] = RECIPIENT
    msg_body = MIMEMultipart('alternative')
    textpart = MIMEText(BODY_TEXT.encode(CHARSET), 'plain', CHARSET)
    htmlpart = MIMEText(BODY_HTML.encode(CHARSET), 'html', CHARSET)
    msg_body.attach(textpart)
    msg_body.attach(htmlpart)
    att = MIMEApplication(open(ATTACHMENT, 'rb').read())
    att.add_header('Content-Disposition', 'attachment',
                   filename=os.path.basename(ATTACHMENT))
    msg.attach(msg_body)
    msg.attach(att)
    # Provide the contents of the email.
    response = ses.send_raw_email(
        Source=SENDER,
        Destinations=[
            RECIPIENT
        ],
        RawMessage={
            'Data': msg.as_string(),
        }
    )
    print("Email sent! Message ID:"),
    print(response['MessageId'])


def config_reporter(event, lambda_context):
    create_report(AGGREGATOR_NAME, today, filename)
    send_email(today, SENDER, RECIPIENT, filename)