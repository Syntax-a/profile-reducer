# GitHub Profile Image Reducer

A simple Python application with a Graphical User Interface (GUI) to help you reduce the file size of images to be suitable for GitHub profile pictures (which have a 1MB limit). The script aims to get the image under 1MB while preserving quality and handling transparency.


## Features

*   **User-Friendly GUI:** Easy-to-use interface built with Tkinter.
*   **Image Selection:** Select images via a standard file dialog.
*   **"Save As..." Dialog:** Choose where to save your processed image and what to name it.
*   **Format Handling:**
    *   Converts opaque images (or those without necessary transparency) to JPEG for good compression.
    *   Preserves transparency by saving as PNG.
    *   Processes the first frame of GIF files.
*   **Size Reduction:**
    *   Iteratively reduces JPEG quality.
    *   Scales down image dimensions if quality reduction isn't enough or for PNGs.
*   **Target:** Aims for a file size strictly under 1MB.
*   **Preview:** Shows a small thumbnail of the selected image.

## Requirements

*   Python 3.x
*   Pillow (Python Imaging Library): `Pillow`
    *   `ImageTk` from Pillow is used for displaying images in the GUI.
*   Tkinter (usually included with standard Python installations)

## Installation & Setup

1.  **Clone the repository (or download the `image_reducer.py` script):**
    ```bash
    git clone https://github.com/Syntax-a/profile-reducer.git
    cd profile-reducer
    ```

2.  **Create and activate a virtual environment (recommended):**
    ```bash
    python -m venv venv
    # On Windows:
    venv\Scripts\activate
    # On macOS/Linux:
    source venv/bin/activate
    ```

3.  **Install the required Python package (Pillow):**
    ```bash
    pip install Pillow
    ```

## How to Use

1.  Ensure you have completed the Installation & Setup steps.
2.  Run the script from your terminal:
    ```bash
    python image_reducer.py
    ```
3.  The application window will open.
    *   Click the "**Select Image**" button to choose the image file you want to process (supports JPG, JPEG, PNG, GIF).
    *   A thumbnail preview of your selected image will appear.
    *   Click the "**Process Image**" button.
    *   If processing is successful, a "**Save As...**" dialog will appear. Choose a location and filename for your processed image. The script will suggest an appropriate file extension (`.jpg` or `.png`).
    *   A success message will confirm the details of the processed image.
4.  Your reduced image is now ready to be uploaded to GitHub!

## Notes

*   The script prioritizes getting the file size under 1MB. This might involve reducing dimensions below GitHub's recommended 500x500 pixels for very large or hard-to-compress images. A warning will be shown if this happens.
*   For animated GIF files, only the first frame is processed and saved as a static image (PNG or JPEG).
*   Console output provides detailed logging of the reduction process.

## Future Ideas 

*   Command-line interface mode.
*   Option to specify target dimensions.
*   Batch processing.

---

*Feel free to contribute or report issues!*