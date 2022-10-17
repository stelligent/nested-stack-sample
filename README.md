# Simple Nested Stack Demo

## Description
Through the use of nested stacks, CloudFormation templates can be modularized and standardized. For example, a VPC could have a requirement that certain NACLs, security groups, or other resources that need to be present for compliance or security reasons. An ECS cluster/Service may require resources outside the standard configuration. The list of possibilities is endless. Nested stacks allow you to implement stacks as separate templates that can be pulled from many locations, and instead of deploying each stack individually and having to remember to deploy the stacks in the correct order (i.e cross-stack reference). Nested stacks allow you to make changes to the various cloud formation templates, and deploy only the master template. CloudFormation will then determine which child stacks need to have updates.

## The Architecture
The architecture of this application is very simple, there's a master stack that deploys a VPC and an EC2. The master template has two nested stacks. One for the VPC and another for the EC2 instance being created.

## Requirements
You will need credentials for an AWS account, and an S3 bucket ready to go for uploading the templates to that bucket for CloudFormation to use.

## Deploying the stack
In this repository, there's a Python script, using Boto3 that can create, update or delete. The script uploads the templates to S3. Here's how to use it:
1. Create a Python Virtual Environment called venv and activate it.
2. Insatall the requirements.txt file using pip
3. Execute deploy.py with the required parameters.

## Cleaning up
With your Python virtual environment activated, pass the `-d` flag with the stack name to delete your CloudFormation stack.