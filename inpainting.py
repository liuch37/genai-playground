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

def inpaint_with_mask_image(pil_image, prompt, mask_image):
    """
    Perform inpainting using Nova Canvas with mask image
    
    Args:
        pil_image (PIL): The input image
        prompt (str): Text prompt describing what to generate
        mask_image (PIL): The mask image where black (0) indicates areas to inpaint
                         and white (255) indicates areas to keep unchanged
    """
    try:
        # Initialize Bedrock runtime client
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1',
            config=Config(read_timeout=300)
        )
        
        # Convert input PIL image to base64 string
        input_buffered = io.BytesIO()
        pil_image.save(input_buffered, format="PNG")
        input_image = base64.b64encode(input_buffered.getvalue()).decode('utf8')

        # Convert mask PIL image to base64 string
        mask_buffered = io.BytesIO()
        mask_image.save(mask_buffered, format="PNG")
        mask_base64 = base64.b64encode(mask_buffered.getvalue()).decode('utf8')

        # Prepare request body
        request_body = {
            "taskType": "INPAINTING",
            "inPaintingParams": {
                "text": prompt,
                "negativeText": "bad quality, blurry, distorted, deformed",
                "image": input_image,
                "maskImage": mask_base64
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
    input_image_path = "./images/81GhOZYLMnL._AC_SL1500_.jpg"
    mask_image_path = "./images/81GhOZYLMnL._AC_SL1500_mask.png"
    
    # Load input and mask images
    pil_image = Image.open(input_image_path)
    mask_image = Image.open(mask_image_path)

    # Example prompt
    prompt = "a red apple"

    # Generate inpainting
    result_image = inpaint_with_mask_image(
        pil_image=pil_image,
        prompt=prompt,
        mask_image=mask_image
    )

    # Display the result image
    result_image.show()  # Basic PIL image display
