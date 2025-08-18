import streamlit as st
import json
import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from streamlit_drawable_canvas import st_canvas

# --- Config ---
LAYOUT_FOLDER = "floor_layouts"
DATA_FOLDER = "floor_data"
FLOORS = {
    "Basement CN-1": "BF-1",
    "Ground Floor CN-1": "GF-1",
    "1st Floor CN-1": "1F-1",
    "2nd Floor CN-1": "2F-1",
    "3rd Floor CN-1": "3F-1",
    "4th Floor CN-1": "4F-1",
    "5th Floor CN-1": "5F-1",
    "6th Floor CN-1": "6F-1",
    "7th Floor CN-1": "7F-1",
    "8th Floor CN-1": "8F-1",
    "9th Floor CN-1": "9F-1",
    "Basement CN-2": "BF-2",
    "Ground Floor CN-2": "GF-2",
    "1st Floor CN-2": "1F-2",
    "2nd Floor CN-2": "2F-2",
    "3rd Floor CN-2": "3F-2",
    "4th Floor CN-2": "4F-2",
    "5th Floor CN-2": "5F-2",
    "6th Floor CN-2": "6F-2",
    "7th Floor CN-2": "7F-2",
    "8th Floor CN-2": "8F-2",
    "9th Floor CN-2": "9F-2",
    "Basement CN-3": "BF-3",
    "Ground Floor CN-3": "GF-3",
    "1st Floor CN-3": "1F-3",
    "2nd Floor CN-3": "2F-3",
    "3rd Floor CN-3": "3F-3",
    "4th Floor CN-3": "4F-3",
    "5th Floor CN-3": "5F-3",
    "6th Floor CN-3": "6F-3",
    "7th Floor CN-3": "7F-3",
    "8th Floor CN-3": "8F-3",
    "9th Floor CN-3": "9F-3",
    "Basement CN-4": "BF-4",
    "Ground Floor CN-4": "GF-4",
    "1st Floor CN-4": "1F-4",
    "2nd Floor CN-4": "2F-4",
    "3rd Floor CN-4": "3F-4",
    "4th Floor CN-4": "4F-4",
    "5th Floor CN-4": "5F-4",
    "6th Floor CN-4": "6F-4",
    "7th Floor CN-4": "7F-4",
    "8th Floor CN-4": "8F-4",
    "9th Floor CN-4": "9F-4",
}

st.set_page_config(layout="wide")
mode = st.sidebar.radio("Choose Mode", ["View Heatmap", "Edit Reader Positions"])

floor_name = st.sidebar.selectbox("Select Floor", list(FLOORS.keys()))
floor_key = FLOORS[floor_name]

layout_path = f"{LAYOUT_FOLDER}/{floor_key}.png"
data_path = f"{DATA_FOLDER}/{floor_key}.json"

# Load layout and data
try:
    img = Image.open(layout_path)
    with open(data_path, 'r') as f:
        config = json.load(f)
    ppm = config["pixels_per_meter"]
    readers = config["readers"]
except Exception as e:
    st.error(f"Error loading layout or data: {e}")
    st.stop()

r_px = int(80 * ppm)

# === VIEW MODE ===
if mode == "View Heatmap":
    st.subheader(f"📡 RFID Coverage – {floor_name}")
    width, height = img.size
    X, Y = np.meshgrid(np.arange(width), np.arange(height))
    Z = np.zeros_like(X, dtype=float)

    for r in readers:
        x0, y0 = r["x"], r["y"]
        sigma = r_px / 2.5
        Z += np.exp(-((X - x0) ** 2 + (Y - y0) ** 2) / (2 * sigma ** 2))

    fig, ax = plt.subplots(figsize=(10, 8))
    ax.imshow(img, extent=[0, width, height, 0])
    heat = ax.imshow(Z, cmap='jet', alpha=0.5, extent=[0, width, height, 0])
    fig.colorbar(heat, ax=ax, label="Signal Strength")
    for i, r in enumerate(readers):
        ax.plot(r["x"], r["y"], 'wo')
        ax.text(r["x"]+5, r["y"]+5, f'R{i+1}', color='white', fontsize=8)
    st.pyplot(fig)

# === EDIT MODE ===
elif mode == "Edit Reader Positions":
    st.subheader(f"🖱 Click to Add RFID Readers – {floor_name}")
    st.markdown("🧠 Tip: Use 'circle' tool to place new readers.")

    # --- Resize image to fit screen ---
    max_width = 1000
    scale_ratio = min(max_width / img.width, 1.0)
    canvas_width = int(img.width * scale_ratio)
    canvas_height = int(img.height * scale_ratio)

    resized_img = img.resize((canvas_width, canvas_height))
    resized_img = resized_img.convert("RGB")  # Ensure RGB format


    # Draw canvas
    canvas_result = st_canvas(
        fill_color="rgba(255, 0, 0, 0.3)",
        stroke_width=1,
        stroke_color="#ff0000",
        background_image=resized_img,
        update_streamlit=True,
        height=canvas_height,
        width=canvas_width,
        drawing_mode="circle",
        key="canvas",
    )

    # Extract new reader positions from drawn objects
    new_readers = []
    if canvas_result.json_data is not None:
        scale_back = img.width / canvas_width
        for obj in canvas_result.json_data["objects"]:
            if obj["type"] == "circle":
                x = (obj["left"] + obj["radius"]) * scale_back
                y = (obj["top"] + obj["radius"]) * scale_back
                new_readers.append({"x": int(x), "y": int(y)})

    st.markdown("### 📍 Current Readers")
    st.json(new_readers)

    if st.button("💾 Save Reader Positions"):
        try:
            with open(data_path, "w") as f:
                json.dump({"pixels_per_meter": ppm, "readers": new_readers}, f, indent=2)
            st.success("✅ Reader positions saved successfully.")
        except Exception as e:
            st.error(f"❌ Error saving reader data: {e}")
