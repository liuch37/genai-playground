'''
python vpp-gradio.py

pip install gradio
'''
import gradio as gr
from PIL import Image, ImageDraw
import numpy as np

# Global variables
bounding_boxes = []  # List to store bounding box coordinates
canvas_size = (1024, 1024)

# Initialize a white canvas
def reset_canvas():
    global bounding_boxes
    bounding_boxes = []
    return np.full((*canvas_size, 3), 255, dtype=np.uint8)

# Draw a bounding box on the right canvas
def draw_bounding_box(image, x1, y1, x2, y2):
    global bounding_boxes
    bounding_boxes.append((x1, y1, x2, y2))
    canvas = Image.fromarray(image)
    draw = ImageDraw.Draw(canvas)
    for box in bounding_boxes:
        draw.rectangle(box, outline="red", width=3)
    return np.array(canvas)

# Insert the left canvas image into the drawn bounding boxes on the right canvas
def insert_image(left_canvas, right_canvas, text_prompt):
    global bounding_boxes
    if not bounding_boxes:
        return right_canvas  # Return as-is if no bounding boxes are drawn

    white_image = np.full((*canvas_size, 3), 255, dtype=np.uint8)
    right_image = Image.fromarray(white_image)
    for box in bounding_boxes:
        x1, y1, x2, y2 = box
        # Resize the left canvas image to fit into the bounding box
        left_image = Image.fromarray(left_canvas).resize((x2 - x1, y2 - y1))
        right_image.paste(left_image, (x1, y1))

    # (Optional) Log or process the text prompt (currently, it's just printed for demonstration)
    print(f"Text prompt: {text_prompt}")

    bounding_boxes.clear()  # Clear bounding boxes after inserting
    return np.array(right_image)

# Gradio UI components
with gr.Blocks() as demo:
    with gr.Row():
        with gr.Column():
            gr.Markdown("### Left Canvas: Upload and Display an Image")
            left_canvas = gr.Image(type="numpy", label="Left Canvas")

        with gr.Column():
            gr.Markdown("### Right Canvas: Draw, Insert, Generate")
            right_canvas = gr.Image(value=reset_canvas(), label="Right Canvas")

    with gr.Row():
        x1_input = gr.Number(label="x1 (Top-Left X)", value=0)
        y1_input = gr.Number(label="y1 (Top-Left Y)", value=0)
        x2_input = gr.Number(label="x2 (Bottom-Right X)", value=100)
        y2_input = gr.Number(label="y2 (Bottom-Right Y)", value=100)

    with gr.Row():
        text_input = gr.Textbox(label="Background Prompt", placeholder="Type your desired background prompt here...")

    with gr.Row():
        draw_button = gr.Button("Draw Bounding Box")
        reset_button = gr.Button("Reset Canvas")
        insert_button = gr.Button("Insert Image")

    # Interactivity
    draw_button.click(draw_bounding_box, inputs=[right_canvas, x1_input, y1_input, x2_input, y2_input], outputs=[right_canvas])
    reset_button.click(reset_canvas, outputs=[right_canvas])
    insert_button.click(insert_image, inputs=[left_canvas, right_canvas, text_input], outputs=[right_canvas])

demo.launch()
