import os
import argparse
import boto3
from botocore.exceptions import ClientError, WaiterError
from pkg_resources import require


def stack_exists(stack_name):
    try:
        stack = cf.describe_stacks(StackName=stack_name).get('Stacks')[0]
    except ClientError:
        print(f'Stack {stack_name} does not exist. Creating!')
        return False

    if stack.get('StackStatus') in ['CREATE_FAILED', 'UPDATE_FAILED', 'ROLLBACK_COMPLETE', 'UPDATE_ROLLBACK_FAILED']:
        print(f'{stack_name} is in status {stack.get("StackStatus")}. Cleaning up now!')
        cleanup_bad_stack(stack)
        return False

    return True


def cleanup_bad_stack(stack):
    print(f'Stack {stack.get("StackName")} cleaning up.')
    try:
        cf.delete_stack(StackName=stack.get('StackName'))
        wait_for_stack(stack.get('StackName'), 'stack_delete_complete')
    except ClientError as e:
        print(f'Stack {stack.get("StackName")} failed to delete with error: {str(e)}. Check the console for more details.')
        raise e


def wait_for_stack(stack_name, status):
    print(f'Waiting for {stack_name} to reach status {status}')
    try:
        waiter = cf.get_waiter(status)
        waiter.wait(StackName=stack_name)
        print(f'{stack_name} reached {status}!')
    except WaiterError as e:
        print(f'Stack {stack_name} failed to reach {status}: {str(e)}. Check the console for more details.')


#Create clients needed for operation

s3 = boto3.client('s3')
cf = boto3.client('cloudformation')

arg_parser = argparse.ArgumentParser(description='Create, update, or destroy a nested stack.')
arg_parser.add_argument('-n', '--stack_name',       help='Name of the stack to create or update', required=True)
arg_parser.add_argument('-d', '--destroy',           help='Destroy stack.', action='store_true')
args = arg_parser.parse_args()

template_urls = {}
bucket_name = 'stelligent-demo-nested-stack-bucket'
stack_name = args.stack_name


if args.destroy:
    print(f'Destroying {stack_name}')
    cf.delete_stack(StackName=stack_name)
    wait_for_stack(stack_name, 'stack_delete_complete')
    print(f'Stack {stack_name} deleted successfully')
else:
    for x in os.listdir():
        if x.endswith('.yml'):
            s3.upload_file(x, bucket_name, x)
            if 'master' in x:
                template_urls['master'] = f'https://s3-{os.environ["AWS_REGION"]}.amazonaws.com/{bucket_name}/{x}'
            if 'EC2' in x:
                template_urls['instance'] = f'https://s3-{os.environ["AWS_REGION"]}.amazonaws.com/{bucket_name}/{x}'
            if 'vpc' in x:
                template_urls['vpc'] = f'https://s3-{os.environ["AWS_REGION"]}.amazonaws.com/{bucket_name}/{x}'

    # Deploy!
    if not stack_exists(stack_name):
        cf.create_stack(
            StackName=stack_name,
            TemplateURL=template_urls.get('master'),
            Parameters=[
                {
                    'ParameterKey': 'VPCTemplateURL',
                    'ParameterValue': template_urls.get('vpc')
                },
                {
                    'ParameterKey': 'EC2TemplateURL',
                    'ParameterValue': template_urls.get('instance')
                }
            ],
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND']
        )

        wait_for_stack(stack_name, 'stack_create_complete')

    else:
        print(f'Updating {stack_name}...')
        cf.update_stack(
            StackName=stack_name,
            TemplateURL=template_urls.get('master'),
            Parameters=[
                {
                    'ParameterKey': 'VPCTemplateURL',
                    'ParameterValue': template_urls.get('vpc')
                },
                {
                    'ParameterKey': 'EC2TemplateURL',
                    'ParameterValue': template_urls.get('instance')
                }
            ],
            Capabilities=['CAPABILITY_IAM', 'CAPABILITY_NAMED_IAM', 'CAPABILITY_AUTO_EXPAND']
        )

        wait_for_stack(stack_name, 'stack_update_complete')
        print(f'Stack {stack_name} update completed!')
