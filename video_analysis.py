'''
Use Bedrock Data Automation to analyze a video.

'''
import boto3
import os
import json
from botocore.exceptions import ClientError
from datetime import datetime
import time

def get_or_create_project(client):
    """Get existing project or create a new one"""
    try:
        response = client.create_data_automation_project(
            projectName="video-analysis-project",
            standardOutputConfiguration={
                "video": {
                    "extraction": {
                        # Required parameters
                        "category": {
                            "state": "ENABLED"
                        },
                        "boundingBox": {
                            "state": "ENABLED"
                        }
                    }
                }
            }
        )
        print("Created new project")
        return response['projectArn']
    except client.exceptions.ConflictException:
        # If project exists, list projects and find the existing one
        try:
            response = client.list_data_automation_projects()
            if 'projects' in response:
                for project in response['projects']:
                    if project['projectName'] == "video-analysis-project":
                        print("Using existing project")
                        return project['projectArn']
            else:
                print("No projects found in response")
                raise Exception("Could not find existing project")
                
        except ClientError as e:
            print(f"Error listing projects: {e}")
            raise
    except ClientError as e:
        print(f"Error creating project: {e}")
        raise

def analyze_video(runtime_client, project_arn, video_path):
    """Analyze a video using BDA"""
    try:
        # First, upload the video to S3
        bucket_name = "bda-video-analysis-west-2"  # Replace with your S3 bucket name
        s3_key = f"input/{os.path.basename(video_path)}"
        s3_client = boto3.client('s3')
        
        # Upload video to S3
        print(f"Uploading video to S3...")
        with open(video_path, 'rb') as file:
            s3_client.upload_fileobj(file, bucket_name, s3_key)
        
        # Configure input and output
        input_config = {
            "s3Uri": f"s3://{bucket_name}/{s3_key}"
        }
        
        output_config = {
            "s3Uri": f"s3://{bucket_name}/output/"  # Output directory in S3
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
            
            if status == 'COMPLETED':
                return status_response
            elif status in ['FAILED', 'CANCELLED', 'ServiceError']:
                error_message = status_response.get('errorMessage', 'No error message provided')
                error_code = status_response.get('errorCode', 'No error code provided')
                raise Exception(f"Job failed with status: {status}, Error Code: {error_code}, Message: {error_message}")
            
            time.sleep(10)  # Wait 10 seconds before checking again
            
    except ClientError as e:
        print(f"Error analyzing video: {e}")
        raise

def save_metadata(results, video_path, output_path):
    """Save all analysis results to a single metadata.json file"""
    if 'body' in results:
        body = json.loads(results['body'].read().decode())
        
        # Create metadata structure
        metadata = {
            "video_path": video_path,
            "analysis_timestamp": datetime.now().isoformat(),
            "analysis_results": body
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Save metadata to JSON file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=4)

def main():
    # Initialize BDA clients
    bda_client = boto3.client('bedrock-data-automation', region_name='us-west-2')
    bda_runtime_client = boto3.client('bedrock-data-automation-runtime', region_name='us-west-2')

    # Path to your video
    video_path = "./videos/2235742-hd_1280_720_30fps.mp4"  # Replace with your video path
    
    # Output path for metadata.json
    output_path = "metadata.json"

    try:
        # Get or create a BDA project
        project_arn = get_or_create_project(bda_client)
        print(f"Using project with ARN: {project_arn}")

        # Analyze the video and get results directly
        print("Starting video analysis...")
        results = analyze_video(bda_runtime_client, project_arn, video_path)
        
        # Save results to metadata.json
        print(f"Saving analysis results to {output_path}...")
        save_metadata(results, video_path, output_path)
        print("Analysis complete! Results have been saved to metadata.json")

    except Exception as e:
        print(f"An error occurred: {e}")
        # Print the full stack trace for debugging
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
