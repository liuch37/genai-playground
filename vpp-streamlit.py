'''
streamlit run vpp-streamlit.py

pip install streamlit streamlit-drawable-canvas
'''
import streamlit as st
from streamlit_drawable_canvas import st_canvas
from PIL import Image, ImageDraw
import numpy as np

# Set up the page layout
st.set_page_config(page_title="Content Generation", layout="wide")

# Initialize the canvas size and a blank white canvas
canvas_size = (1024, 1024)
blank_canvas = np.full((*canvas_size, 3), 255, dtype=np.uint8)

# Sidebar for user controls
st.sidebar.header("Controls")
uploaded_image = st.sidebar.file_uploader("Upload an Image for Product Canvas", type=["png", "jpg", "jpeg"])
text_prompt = st.sidebar.text_input("Enter a Text Prompt for your Background", placeholder="Type your background prompt here...")
insert_button = st.sidebar.button("Insert Image")
reset_button = st.sidebar.button("Reset Composition Canvas")

# Left Canvas
st.subheader("Product Canvas")
if uploaded_image:
    left_canvas = Image.open(uploaded_image).convert("RGB")
    left_canvas_np = np.array(left_canvas)
    st.image(left_canvas_np, caption="Product Canvas", use_container_width=True)
else:
    st.info("Upload an image to display on the Product Canvas.")

# Right Canvas
st.subheader("Position Canvas: Draw a Bounding Box for Product Placement")
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

# Display the updated right canvas
st.subheader("Composition Canvas")
if "canvas_image" in st.session_state:
    st.image(st.session_state["canvas_image"], caption="Composition Canvas", use_container_width=True)
