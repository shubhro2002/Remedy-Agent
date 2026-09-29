#!/bin/bash
echo "Initializing SecOps environment..."

# 1. Create a dummy S3 bucket
awslocal s3api create-bucket --bucket company-confidential-data

# 2. Intentionally make it publicly readable (Security Vulnerability!)
awslocal s3api put-bucket-acl --bucket company-confidential-data --acl public-read

# 3. Add a dummy file to simulate sensitive data
echo "CONFIDENTIAL: API_KEY=xyz123" > /tmp/secrets.txt
awslocal s3 cp /tmp/secrets.txt s3://company-confidential-data/secrets.txt

echo "Misconfigured S3 bucket 'company-confidential-data' created successfully."