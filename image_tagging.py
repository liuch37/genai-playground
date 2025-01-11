import boto3
import base64
import json
import io
from botocore.config import Config
from PIL import Image

def get_product_description(pil_image, max_words=3):
    """
    Generate a short product description using Claude V2 for the main product in the image
    
    Args:
        pil_image (PIL.Image): Input PIL image
        max_words (int): Maximum number of words in the description
    
    Returns:
        str: Short product description
    """
    try:
        # Initialize Bedrock runtime client
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name='us-east-1',
            config=Config(read_timeout=120)
        )

        # Convert PIL image to base64
        buffered = io.BytesIO()
        pil_image.save(buffered, format="PNG")
        image_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')

        # Prepare the prompt
        prompt = f"""
        Look at this image and provide a concise description of the main product shown, using {max_words} words or less.
        Focus only on identifying the central product.
        """

        # Prepare the messages with both text and image
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]

        # Prepare request body for Claude
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 100,
            "messages": messages
        }

        # Invoke Claude model
        response = bedrock.invoke_model(
            body=json.dumps(body),
            modelId='anthropic.claude-3-sonnet-20240229-v1:0',
            accept='application/json',
            contentType='application/json'
        )

        # Process response
        response_body = json.loads(response.get('body').read())
        description = response_body['content'][0]['text'].strip()

        # Ensure description is no more than max_words
        words = description.split()
        if len(words) > max_words:
            description = ' '.join(words[:max_words])

        return description

    except Exception as e:
        print(f"Error generating description: {str(e)}")
        raise

if __name__ == "__main__":
    # Example usage
    input_image_path = "./images/81T-766EbnL._AC_SL1500_.jpg"
    image = Image.open(input_image_path)
    
    # Get product description
    description = get_product_description(image)
    print(f"Product description: {description}")
