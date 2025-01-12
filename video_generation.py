import boto3
import base64
from PIL import Image
import io
import json
import time
import random
import tempfile

def generate_video_from_image(image: Image.Image, prompt: str, output_path: str):
    """
    Generate a video using Amazon Nova Reel from a reference image and text prompt
    
    Args:
        image (PIL.Image): Input reference image
        prompt (str): Text prompt describing the desired video
        output_path (str): Path to save the output video
    
    Returns:
        bool: True if video generation was successful
    """
    # Resize PIL image
    image = image.resize((1280, 720), Image.Resampling.LANCZOS)

    # Convert PIL image to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

    # Create Bedrock Runtime client
    bedrock = boto3.client(
        service_name='bedrock-runtime',
        region_name='us-east-1'  # Nova Reel is available in us-east-1
    )

    # temp variables
    S3_DESTINATION_BUCKET = "video-gen"
    MODEL_ID = "amazon.nova-reel-v1:0"
    SLEEP_TIME = 30

    # Prepare model input
    model_input = {
        "taskType": "TEXT_VIDEO",
        "textToVideoParams": {
            "text": prompt,
            "images": [{ "format": "png", "source": { "bytes": image_base64 } }]
        },
        "videoGenerationConfig": {
            "durationSeconds": 6,
            "fps": 24,
            "dimension": "1280x720",
            "seed": random.randint(0, 2147483648)
        }
    }
    
    invocation = bedrock.start_async_invoke(
        modelId=MODEL_ID,
        modelInput=model_input,
        outputDataConfig={"s3OutputDataConfig": {"s3Uri": f"s3://{S3_DESTINATION_BUCKET}"}}
    )

    invocation_arn = invocation["invocationArn"]
    s3_prefix = invocation_arn.split('/')[-1]
    s3_location = f"s3://{S3_DESTINATION_BUCKET}/{s3_prefix}"
    print(f"\nS3 URI: {s3_location}")

    while True:
        response = bedrock.get_async_invoke(
            invocationArn=invocation_arn
        )
        status = response["status"]
        print(f"Status: {status}")
        if status != "InProgress":
            break
        time.sleep(SLEEP_TIME)

    if status == "Completed":
        print(f"\nVideo is ready at {s3_location}/output.mp4")
    else:
        print(f"\nVideo generation status: {status}")
    
    # Download the video from s3
    s3_client = boto3.client("s3")
    #s3_client.download_file(S3_DESTINATION_BUCKET, f"{s3_prefix}/output.mp4", output_path)
    #print(f"\nVideo is downloaded at {output_path}")

    # Create a temporary file to store the video
    with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
        # Download video from S3 to temporary file
        s3_client.download_fileobj(S3_DESTINATION_BUCKET, f"{s3_prefix}/output.mp4", tmp_file)
        tmp_file.seek(0)    
        # Read the video file
        video_bytes = open(tmp_file.name, 'rb').read()
    
    return video_bytes

# Example usage
if __name__ == "__main__":
    # Load your image
    input_image = Image.open("./images/61F3p01-OpL._AC_SL1500_.jpg")
    
    # Your prompt describing the desired video
    prompt = "drone view flying over the product. 4k, photorealistic, shallow depth of field."
    
    # Generate the video
    video_bytes = generate_video_from_image(
        image=input_image,
        prompt=prompt,
        output_path="output_video.mp4"
    )

    print(video_bytes)