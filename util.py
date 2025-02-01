import cv2
import math
import numpy as np

def rotation(x1, y1, angle, width, height):
    # Convert angle to radians
    theta = angle * (3.141592653589793 / 180)

    # Original corners relative to top-left (x1,y1) before rotation
    # (x1,y1) is already known
    # Calculate other corners relative to (x1,y1)
    x2 = width  # top-right
    y2 = 0
    x3 = width  # bottom-right
    y3 = height
    x4 = 0      # bottom-left
    y4 = height

    # Rotation matrix multiplication for each point
    # For each point we need to:
    # x' = x*cos(theta) - y*sin(theta)
    # y' = x*sin(theta) + y*cos(theta)
    
    # Top-right corner (x2,y2)
    x2_rot = x2 * math.cos(theta) - y2 * math.sin(theta)
    y2_rot = x2 * math.sin(theta) + y2 * math.cos(theta)
    
    # Bottom-right corner (x3,y3)
    x3_rot = x3 * math.cos(theta) - y3 * math.sin(theta)
    y3_rot = x3 * math.sin(theta) + y3 * math.cos(theta)
    
    # Bottom-left corner (x4,y4)
    x4_rot = x4 * math.cos(theta) - y4 * math.sin(theta)
    y4_rot = x4 * math.sin(theta) + y4 * math.cos(theta)

    # Add the offset of (x1,y1) to get final coordinates
    return [
        (int(x1), int(y1)),  # top-left (original point)
        (int(x1 + x2_rot), int(y1 + y2_rot)),  # top-right
        (int(x1 + x3_rot), int(y1 + y3_rot)),  # bottom-right
        (int(x1 + x4_rot), int(y1 + y4_rot))   # bottom-left
    ]

def homography_transform(product_img, canvas_img, coordinates):
    # Convert PIL image to OpenCV format
    product_img_cv = np.array(product_img)
    canvas_img_cv = np.array(canvas_img)

    # Get the size of the product image
    h, w = product_img_cv.shape[:2]

    # Create the source points (corners of the product image)
    pts_src = np.array([
        [0, 0],           # top-left
        [w-1, 0],         # top-right
        [w-1, h-1],       # bottom-right
        [0, h-1]          # bottom-left
    ], dtype=np.float32)

    # Convert destination coordinates to numpy array
    pts_dst = np.array(coordinates, dtype=np.float32)
    
    # Calculate homography matrix
    H, _ = cv2.findHomography(pts_src, pts_dst)
    
    # Warp the product image onto the white canvas
    warped = cv2.warpPerspective(product_img_cv, H, (canvas_img_cv.shape[1], canvas_img_cv.shape[0]), 
                                dst=canvas_img_cv, 
                                borderMode=cv2.BORDER_TRANSPARENT)

    return warped
