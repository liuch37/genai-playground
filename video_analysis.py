'''
Use Bedrock Data Automation to analyze a video.

'''
import boto3
import os
import json
from botocore.exceptions import ClientError
from datetime import datetime
import time

def read_json_from_s3(bucket_name, file_key):
    """
    Read a JSON file from S3 and return its contents as a Python dictionary

    Parameters:
        bucket_name (str): Name of the S3 bucket
        file_key (str): Path to the JSON file in the bucket

    Returns:
        dict: Contents of the JSON file
    """
    try:
        # Create an S3 client
        s3_client = boto3.client('s3', region_name='us-west-2')  # Replace with your region

        # Get the object from S3
        response = s3_client.get_object(
            Bucket=bucket_name,
            Key=file_key
        )

        # Read the JSON content
        json_content = response['Body'].read().decode('utf-8')

        # Parse JSON into a Python dictionary
        data = json.loads(json_content)

        return data

    except Exception as e:
        print(f"Error reading JSON from S3: {str(e)}")
        raise

def parse_s3_uri(s3_uri):
    """
    Parse an S3 URI into bucket name and key

    Parameters:
        s3_uri (str): S3 URI (e.g., 's3://bucket-name/path/to/file.json')

    Returns:
        tuple: (bucket_name, file_key)
    """
    # Remove 's3://' prefix
    path = s3_uri.replace('s3://', '')

    # Split into bucket and key
    parts = path.split('/', 1)
    bucket_name = parts[0]
    file_key = parts[1] if len(parts) > 1 else ''

    return bucket_name, file_key

def get_or_create_project(client):
    """Get existing project or create a new one"""
    try:
        response = client.create_data_automation_project(
            projectName=f"video-analysis-job-{int(time.time())}",
            standardOutputConfiguration={
                "video": {
                    "extraction": {
                        "category": {
                            "state": "ENABLED",
                                "types": ["CONTENT_MODERATION","TEXT_DETECTION","TRANSCRIPT"]
                        },
                        "boundingBox": {
                            "state": "DISABLED"
                        }
                    },
                    "generativeField": {
                        "state": "ENABLED",
                        "types": ["VIDEO_SUMMARY","SCENE_SUMMARY","IAB"]
                    }
                }
            }
        )
        print("Created new project")
        return response['projectArn']
    except ClientError as e:
        print(f"Error creating project: {e}")
        raise

def analyze_video(runtime_client, project_arn):
    """Analyze a video using BDA"""
    try:
        # First, upload the video to S3
        bucket_name = "testing-video-01242025"  # Replace with your S3 bucket name
        s3_key = "sample-video/2U_ulXkfXqQ.mp4"

        # Configure input and output
        input_config = {
            "s3Uri": f"s3://{bucket_name}/{s3_key}"
        }

        output_config = {
            "s3Uri": f"s3://{bucket_name}/metadata-output-{int(time.time())}"  # Output directory in S3
        }

        # Invoke BDA asynchronously
        response = runtime_client.invoke_data_automation_async(
            inputConfiguration=input_config,
            outputConfiguration=output_config,
            dataAutomationConfiguration={
                "dataAutomationArn": project_arn,
                "stage": "LIVE"
            }
        )

        # Get the invocation ARN from the response
        invocation_arn = response.get('invocationArn')
        print(f"Started async job with invocation ARN: {invocation_arn}")

        if not invocation_arn:
            raise Exception("No invocation ARN received in response")

        # Poll for job completion
        while True:
            status_response = runtime_client.get_data_automation_status(
                invocationArn=invocation_arn
            )

            # Print the full status response for debugging
            print(f"Full status response: {json.dumps(status_response, indent=2, default=str)}")

            status = status_response.get('status')
            print(f"Job status: {status}")

            if status == 'Success':
                job_metadata_s3_uri = status_response["outputConfiguration"]['s3Uri']
                # Parse the S3 URI
                bucket_name, file_key = parse_s3_uri(job_metadata_s3_uri)
                # Read and parse the JSON file
                job_metadata = read_json_from_s3(bucket_name, file_key)
                video_data_s3_uri = job_metadata['output_metadata'][0]['segment_metadata'][0]['standard_output_path']
                # Parse the S3 URI
                bucket_name, file_key = parse_s3_uri(video_data_s3_uri)
                # Read and parse the JSON file
                video_metadata = read_json_from_s3(bucket_name, file_key)
                return video_metadata
            elif status in ['Failed', 'Cancelled', 'ServiceError']:
                error_message = status_response.get('errorMessage', 'No error message provided')
                error_code = status_response.get('errorCode', 'No error code provided')
                raise Exception(f"Job failed with status: {status}, Error Code: {error_code}, Message: {error_message}")

            time.sleep(10)  # Wait 10 seconds before checking again

    except ClientError as e:
        print(f"Error analyzing video: {e}")
        raise

def main():
    # Initialize BDA clients
    bda_client = boto3.client('bedrock-data-automation', region_name='us-west-2')
    bda_runtime_client = boto3.client('bedrock-data-automation-runtime', region_name='us-west-2')

    # Output path for metadata.json
    output_path = "video_metadata.json"

    try:
        # Get or create a BDA project
        project_arn = get_or_create_project(bda_client)
        print(f"Using project with ARN: {project_arn}")

        # Analyze the video and get results directly
        print("Starting video analysis...")
        video_metadata = analyze_video(bda_runtime_client, project_arn)
        print(video_metadata)

        # Save results to metadata.json
        print(f"Saving analysis results to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(video_metadata, f, indent=4)

        print(f"Analysis complete! Results have been saved to {output_path}")

    except Exception as e:
        print(f"An error occurred: {e}")
        # Print the full stack trace for debugging
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()