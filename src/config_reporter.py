
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
import os
import boto3
import datetime
import json
import csv
from botocore.exceptions import ClientError
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication

today = datetime.datetime.now().strftime("%Y-%m-%d")  # Currnent day
aggregator_name = os.environ['aggregator_name']  # AWS Config Aggregator name
SENDER = os.environ['SENDER']  # SES Sender address
RECIPIENT = os.environ['RECIPIENT']  # SES Recipient address
filename = f'/tmp/changed_resources-{today}.csv'  # CSV report filename

# Generate the resource link to AWS Console UI
def get_link(AWS_REGION, RESOURCE_ID, RESOURCE_TYPE):
    url = f'https://{AWS_REGION}.console.aws.amazon.com/config/home?region={AWS_REGION}#/resources/timeline?resourceId={RESOURCE_ID}&resourceType={RESOURCE_TYPE}'
    return url


# Generate the CSV Report
def create_report(aggregator_name, today):
    client = boto3.client('config')
    response = client.select_aggregate_resource_config(
        Expression=f"SELECT * WHERE configurationItemCaptureTime LIKE '{today}%'",
        ConfigurationAggregatorName=aggregator_name
    )
    changed_resources = response["Results"]
    json_list = [json.loads(line) for line in changed_resources]
    # Transform the JSON response to CSV file
    for resource in json_list:
        AWS_REGION = resource['awsRegion']
        RESOURCE_ID = resource['resourceId']
        RESOURCE_TYPE = resource['resourceType']
        resource['Link'] = get_link(AWS_REGION, RESOURCE_ID, RESOURCE_TYPE)
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


def send_email(today, SENDER, RECIPIENT):
    # The subject line for the email.
    SUBJECT = f"AWS Config changes report {today}"
    ATTACHMENT = filename
    BODY_TEXT = "Hello,\r\nPlease see the attached file which includes the contains made during the last day."

    # The HTML body of the email.
    BODY_HTML = """\
    <html>
    <head></head>
    <body>
    <h1>Hello!</h1>
    <p>Hello, please see the attached file which contains the changes made during the last day.</p>
    </body>
    </html>
    """
    CHARSET = "utf-8"
    client = boto3.client('ses')
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
    try:
        # Provide the contents of the email.
        response = client.send_raw_email(
            Source=SENDER,
            Destinations=[
                RECIPIENT
            ],
            RawMessage={
                'Data': msg.as_string(),
            }
        )
    # Display an error if something goes wrong.
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent! Message ID:"),
        print(response['MessageId'])


def config_reporter(event, lambda_context):
    create_report(aggregator_name, today)
    send_email(today, SENDER, RECIPIENT)
