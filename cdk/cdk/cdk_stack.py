
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
from typing_extensions import runtime
from async_timeout import timeout
from aws_cdk.aws_events import Rule, Schedule
import aws_cdk.aws_events_targets as targets
from aws_cdk.aws_iam import Role
from aws_cdk import (
    Duration,
    Stack,
    aws_lambda_python_alpha as lambda_,
    aws_lambda,
    aws_iam as iam,
)
import aws_cdk
from constructs import Construct

class DailyConfigReporter(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        aggregator = aws_cdk.CfnParameter(
            self,
            "aggregator",
            type="String",
            default='aggregator',
            description="Name of AWS Config Aggregator"
        )

        RECIPIENT = aws_cdk.CfnParameter(
            self,
            "RECIPIENT",
            type="String",
            default='RECIPIENT@EMAIL.COM',
            description="SES recipient email address"
        )
        SENDER = aws_cdk.CfnParameter(
            self,
            "SENDER",
            type="String",
            default='SENDER@EMAIL.COM',
            description="SES sender email address"
        )
        config_reporter_lambda = lambda_.PythonFunction(self, "config_reporter",
            entry="../src/",  # required
            runtime=aws_lambda.Runtime.PYTHON_3_8, 
            index="config_reporter.py", 
            handler="config_reporter",
            timeout=Duration.seconds(60),
            environment={
        "aggregator_name": aggregator.value_as_string,
        "SENDER": SENDER.value_as_string,
        "RECIPIENT": RECIPIENT.value_as_string}
        )
        config_reporter_lambda.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                'config:SelectAggregateResourceConfig',
                'ses:SendRawEmail'
            ],
            resources=[
                '*',
            ],
        ))
        rule = Rule(self, "ConfigDailyReporterCW",
        schedule=Schedule.cron(minute="50", hour="20")
    )
        rule.add_target(targets.LambdaFunction(config_reporter_lambda))