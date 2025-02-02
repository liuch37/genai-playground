import cv2
import numpy as np
from PIL import Image

def create_mask_from_bbox(image_path, bbox, output_path):
    """
    Create a binary mask with black rectangle in the bounding box region and white elsewhere
    
    Args:
        image_path (str): Path to the input image
        bbox (tuple): Bounding box coordinates (xmin, ymin, xmax, ymax)
        output_path (str): Path to save the mask PNG file
    """
    # Read the image to get dimensions
    image = cv2.imread(image_path)
    if image is None:
        raise ValueError(f"Could not load image from {image_path}")
    
    # Create a white mask of the same size as input image
    mask = np.full(image.shape[:2], 255, dtype=np.uint8)
    
    # Extract bbox coordinates
    xmin, ymin, xmax, ymax = bbox
    
    # Fill the bounding box region with black (0)
    mask[ymin:ymax, xmin:xmax] = 0
    
    # Save the mask as PNG
    cv2.imwrite(output_path, mask)
    
    return mask

# Example usage
if __name__ == "__main__":
    image_path = "./images/81GhOZYLMnL._AC_SL1500_.jpg"
    bbox = (328, 780, 700, 1112)  # (xmin, ymin, xmax, ymax)
    output_path = "./images/81GhOZYLMnL._AC_SL1500_mask.png"

    mask = create_mask_from_bbox(image_path, bbox, output_path)
