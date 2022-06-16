
# AWS Config Daily Reporter

Security Group Report Generator provides you a centralized, point in time report of your security groups policy.  
The script outputs an excel table:



### Prerequisites
Amazon Simple Email Service
AWS Config Aggregator 
AWS CDK


### Architecture
1. Amazon CloudWatch event - will trigger Lambda every day at 11:50 PM.
2. AWS Lambda - will run Python3 code which includes an AWS Config Query and SendEmail using SES.
3. AWS Config - aggregator which will get a query from the Lambda function.
4. Amazon Simple Email Service - will be used to send an email with the CSV file.

![](draw/config-daily-reporter.drawio.png)

### Getting Started


1. ```git clone https://gitlab.aws.dev/dbbegimh/config-daily-reporter```
2. ```cd config-daily-reporter/cdk```
3. ```cdk bootstrap```
4. ```cdk deploy --parameters aggregator=<aggregator name> --parameters RECIPIENT=<recipient email address> --parameters SENDER=<sender email address>```

Replace the parameters as follows:

* aggregator - Name of AWS Config Aggregator.
* RECIPIENT - Email recipient that will get the csv report.
* SENDER - Email sender as configured on SES.


Sample report can be found [here](sample_report.csv)
## Security
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License
This library is licensed under the Apache 2.0 License. See the LICENSE file.

