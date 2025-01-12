import boto3
import base64
import json
import logging
from PIL import Image
import numpy as np
import io
import random
from botocore.config import Config
from botocore.exceptions import ClientError

def outpaint_with_mask_prompt(pil_image, prompt, mask_prompt):
    """
    Perform outpainting using Nova Canvas with mask prompt
    
    Args:
        pil_image (PIL): The input image
        prompt (str): Text prompt describing what to generate
        mask_prompt (str): Text prompt describing what to mask in the image
    """
    try:
        # Initialize Bedrock runtime client
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1',
            config=Config(read_timeout=300)
        )
        
        # Convert PIL image to base64 string
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        input_image = base64.b64encode(buffered.getvalue()).decode('utf8')

        # Prepare request body
        request_body = {
            "taskType": "OUTPAINTING",
            "outPaintingParams": {
                "text": prompt,
                "negativeText": "bad quality, blurry, distorted, deformed",
                "image": input_image,
                "maskPrompt": mask_prompt,
                "outPaintingMode": "PRECISE"
            },
            "imageGenerationConfig": {
                "numberOfImages": 1,
                "height": 512,
                "width": 512,
                "cfgScale": 8.0,
                "seed": random.randint(0, 2147483648)
            }
        }

        # Invoke Nova Canvas model
        response = bedrock.invoke_model(
            body=json.dumps(request_body),
            modelId='amazon.nova-canvas-v1:0',
            accept='application/json',
            contentType='application/json'
        )

        # Process response
        response_body = json.loads(response.get("body").read())
        
        # Check for errors
        if response_body.get("error"):
            raise Exception(f"Image generation error: {response_body.get('error')}")

        # Get generated image
        base64_image = response_body.get("images")[0]
        image_bytes = base64.b64decode(base64_image.encode('ascii'))
    
        # Convert to PIL Image
        generated_image = Image.open(io.BytesIO(image_bytes))

        return generated_image

    except ClientError as e:
        print(f"AWS service error: {str(e)}")
        raise
    except Exception as e:
        print(f"Error generating image: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    # Replace with your input image path
    input_image_path = "./images/81T-766EbnL._AC_SL1500_.jpg"
    pil_image = Image.open(input_image_path)

    # Example prompts
    prompt = "a beautiful mountain landscape with snow peaks and clear blue sky"
    mask_prompt = "tv monitor"

    # Generate outpainting
    result_image = outpaint_with_mask_prompt(
            pil_image=pil_image,  # Fix parameter name
            prompt=prompt,
            mask_prompt=mask_prompt
    )

    # Display the result image
    result_image.show()  # Basic PIL image display
