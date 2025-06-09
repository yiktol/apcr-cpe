import boto3
import json
from botocore.exceptions import ClientError


def get_cognito_credentials(secret_name="CognitoCredentials",region_name="us-east-1"):
    """
    Retrieve Cognito credentials from AWS Secrets Manager
    
    Returns:
        dict: Dictionary containing Cognito credentials
    """
    
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )
    
    try:
        # Get the secret value
        response = client.get_secret_value(SecretId=secret_name)
        
        # Parse the secret string to a dictionary
        if 'SecretString' in response:
            secret = json.loads(response['SecretString'])
            
            # Extract required credentials
            cognito_credentials = {
                'COGNITO_DOMAIN': secret.get('COGNITO_DOMAIN'),
                'COGNITO_USER_POOL_ID': secret.get('COGNITO_USER_POOL_ID'),
                'COGNITO_APP_CLIENT_SECRET': secret.get('COGNITO_APP_CLIENT_SECRET'),
                'COGNITO_APP_CLIENT_ID': secret.get('COGNITO_APP_CLIENT_ID'),
                'COGNITO_REDIRECT_URI': secret.get('COGNITO_REDIRECT_URI'),
                'COGNITO_REDIRECT_URI_AIP_1': secret.get('COGNITO_REDIRECT_URI_AIP_1'),
                'COGNITO_REDIRECT_URI_AIP_2': secret.get('COGNITO_REDIRECT_URI_AIP_2'),
                'COGNITO_REDIRECT_URI_AIP_3': secret.get('COGNITO_REDIRECT_URI_AIP_3'),
                'COGNITO_REDIRECT_URI_AIP_4': secret.get('COGNITO_REDIRECT_URI_AIP_4')
            }
            
            return cognito_credentials
        else:
            # Binary secret
            raise ValueError("Binary secrets not supported for this function")
            
    except ClientError as e:
        # Handle exceptions
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        print(f"Error retrieving secret: {error_code} - {error_msg}")
        raise