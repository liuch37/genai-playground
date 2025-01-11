'''
streamlit run vpp-streamlit.py

pip install streamlit streamlit-drawable-canvas
'''
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw
import numpy as np
from outpainting import outpaint_with_mask_prompt
from image_tagging import get_product_description

# Set up the page layout
st.set_page_config(page_title="Content Generation", layout="wide")

# Initialize the canvas size and a blank white canvas
canvas_size = (512, 512)
blank_canvas = np.full((*canvas_size, 3), 255, dtype=np.uint8)

# Sidebar for user controls
st.sidebar.header("Controls")
uploaded_image = st.sidebar.file_uploader("Upload an Image for Product Canvas", type=["png", "jpg", "jpeg"])
product_description = get_product_description(Image.open(uploaded_image)) if uploaded_image else ""
# Use the product description as default value in text input
product_prompt = st.sidebar.text_input(
    "Enter a Text Prompt for your Product", 
    value=product_description,
    placeholder="Type your product prompt here..."
)
background_prompt = st.sidebar.text_input("Enter a Text Prompt for your Background", placeholder="Type your background prompt here...")
insert_button = st.sidebar.button("Insert Image")
generate_button = st.sidebar.button("Generate Image")
reset_button = st.sidebar.button("Reset Composition Canvas")

# Product Canvas
st.subheader("Product Canvas")
if uploaded_image:
    left_canvas = Image.open(uploaded_image).convert("RGB")
    left_canvas_np = np.array(left_canvas)
    st.image(left_canvas_np, caption="Product Canvas", use_container_width=True)
else:
    st.info("Upload an image to display on the Product Canvas.")

# Create two columns for Position Canvas and Composition Canvas
col1, col2 = st.columns(2)

with col1:
    # Position Canvas
    st.subheader("Position Canvas")
    if reset_button:
        st.session_state["canvas_image"] = blank_canvas.copy()

    # Initialize session state for the canvas
    if "canvas_image" not in st.session_state:
        st.session_state["canvas_image"] = blank_canvas.copy()

    # Interactive drawing canvas
    canvas_result = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",  # Transparent fill
        stroke_width=3,
        stroke_color="red",
        background_color="#FFFFFF",
        background_image=Image.fromarray(blank_canvas.copy()),
        update_streamlit=True,
        height=canvas_size[0],
        width=canvas_size[1],
        drawing_mode="rect",  # Rectangle drawing mode
        key="canvas",
    )

# Process bounding boxes and insert image
if insert_button:
    if uploaded_image and canvas_result.json_data:
        # Extract bounding box data
        objects = canvas_result.json_data.get("objects", [])
        right_image = Image.fromarray(st.session_state["canvas_image"])

        for obj in objects:
            if obj["type"] == "rect":
                x1, y1 = int(obj["left"]), int(obj["top"])
                x2, y2 = x1 + int(obj["width"]), y1 + int(obj["height"])

                # Resize the left canvas image and insert it into the bounding box
                left_resized = left_canvas.resize((x2 - x1, y2 - y1))
                right_image.paste(left_resized, (x1, y1))

        # Update the canvas
        st.session_state["canvas_image"] = np.array(right_image)
    else:
        st.warning("Please upload an image and draw bounding boxes first.")

if generate_button:
    if "canvas_image" in st.session_state and product_prompt and background_prompt:
        # Convert the canvas image to PIL format for processing
        composition_image = Image.fromarray(st.session_state["canvas_image"])

        # Generate the image using the outpainting function
        result_image = outpaint_with_mask_prompt(composition_image, background_prompt, product_prompt)
        st.session_state["canvas_image"] = np.array(result_image) # Update the canvas state
    else:
        st.warning("Please ensure all fields are filled correctly before generating.")

with col2:
    # Composition Canvas
    st.subheader("Composition Canvas")
    if "canvas_image" in st.session_state:
        st.image(st.session_state["canvas_image"], caption="Composition Canvas", width=canvas_size[0])