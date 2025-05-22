import os
from PIL import Image, UnidentifiedImageError, ImageFile, ImageTk # Add ImageTk for GUI
import io

# --- GUI Imports ---
import tkinter as tk
from tkinter import filedialog, messagebox

# --- Constants (from your original script) ---
TARGET_MAX_BYTES = 0.98 * 1024 * 1024
RECOMMENDED_DIMENSION = 500
MIN_DIMENSION = 200
MAX_ITERATIONS = 15
JPEG_QUALITY_STEP = 7
JPEG_MIN_QUALITY = 60
DIMENSION_SCALE_STEP = 0.1

ImageFile.LOAD_TRUNCATED_IMAGES = True

def reduce_image_for_github(input_image_path):
    # Returns: (success_boolean, image_data_bytes, suggested_extension_string, final_w, final_h, final_size_kb)
    # or (False, None, None, None, None, None) on failure

    print(f"Starting reduction for: {input_image_path}")
    if not os.path.exists(input_image_path):
        print(f"Error: Input file not found at '{input_image_path}'")
        return False, None, None, None, None, None

    try:
        img = Image.open(input_image_path)
        original_format = img.format
        original_mode = img.mode
        original_width, original_height = img.size
        initial_size_bytes = os.path.getsize(input_image_path)

        print(f"Image opened:")
        print(f"  Format: {original_format}, Mode: {original_mode}, Dimensions: {original_width}x{original_height}, Size: {initial_size_bytes / 1024:.2f} KB")

        if initial_size_bytes <= TARGET_MAX_BYTES:
            print(f"Image already under target size ({TARGET_MAX_BYTES / 1024:.2f} KB). Optimizing.")
            temp_buffer_small = io.BytesIO()
            current_img_copy = img.copy()
            final_save_format_small = original_format
            extension_small = ".dat" 

            try:
                if original_format == "PNG":
                    final_save_format_small = "PNG"; extension_small = ".png"
                    current_img_copy.save(temp_buffer_small, format="PNG", optimize=True)
                elif original_format == "JPEG":
                    final_save_format_small = "JPEG"; extension_small = ".jpg"
                    current_img_copy.save(temp_buffer_small, format="JPEG", quality=95, optimize=True, progressive=True)
                elif original_format == "GIF":
                    final_save_format_small = "PNG"; extension_small = ".png"
                    current_img_copy.seek(0)
                    if current_img_copy.mode == 'P' and 'transparency' in current_img_copy.info: current_img_copy = current_img_copy.convert("RGBA")
                    elif current_img_copy.mode != 'RGB' and current_img_copy.mode != 'RGBA': current_img_copy = current_img_copy.convert("RGB")
                    current_img_copy.save(temp_buffer_small, format="PNG", optimize=True)
                else: 
                    has_alpha_small = current_img_copy.mode in ('RGBA', 'LA') or \
                                   (current_img_copy.mode == 'P' and 'transparency' in current_img_copy.info)
                    if has_alpha_small:
                        final_save_format_small = "PNG"; extension_small = ".png"
                        if current_img_copy.mode != 'RGBA': current_img_copy = current_img_copy.convert("RGBA")
                        current_img_copy.save(temp_buffer_small, format="PNG", optimize=True)
                    else:
                        final_save_format_small = "JPEG"; extension_small = ".jpg"
                        if current_img_copy.mode != 'RGB': current_img_copy = current_img_copy.convert("RGB")
                        current_img_copy.save(temp_buffer_small, format="JPEG", quality=95, optimize=True, progressive=True)
                
                optimized_data = temp_buffer_small.getvalue()
                final_size_kb = len(optimized_data) / 1024.0
                print(f"Image optimized. Final format: {final_save_format_small}, Final size: {final_size_kb:.2f} KB")
                return True, optimized_data, extension_small, original_width, original_height, final_size_kb
            except Exception as e_save_small:
                print(f"Error optimizing already small image: {e_save_small}.")
                return False, None, None, None, None, None

        print(f"Image needs reduction. Target: < {TARGET_MAX_BYTES / 1024:.2f} KB")
        if original_format == "GIF":
            img.seek(0)
            if img.mode == 'P' and 'transparency' in img.info:
                current_img = Image.new("RGBA", img.size); current_img.paste(img)
            elif img.mode == 'RGBA': current_img = img.copy()
            else: current_img = img.convert('RGB')
            print("Working with the first frame of the GIF, converted to RGBA/RGB.")
        else:
            current_img = img.copy()

        has_alpha = current_img.mode in ('RGBA', 'LA') or (current_img.mode == 'P' and 'transparency' in current_img.info)
        
        if has_alpha and current_img.mode != 'RGBA':
            current_img = current_img.convert('RGBA'); print("Converted image to RGBA to preserve transparency.")
        elif not has_alpha and current_img.mode not in ('RGB', 'L'):
            current_img = current_img.convert('RGB'); print(f"Converted image mode from {original_mode} to RGB.")

        final_processing_save_format = "PNG" if has_alpha else "JPEG"
        final_extension = ".png" if final_processing_save_format == "PNG" else ".jpg"
        print(f"Targeting {final_processing_save_format} format for reduction.")

        base_width, base_height = current_img.size
        current_scale = 1.0
        current_jpeg_quality = 90
        last_attempted_size_bytes = initial_size_bytes
        new_width, new_height = base_width, base_height

        for i in range(MAX_ITERATIONS):
            temp_buffer = io.BytesIO()
            image_to_save_this_iteration = current_img
            
            if current_scale < 1.0:
                iter_new_width = int(base_width * current_scale)
                iter_new_height = int(base_height * current_scale)
                if iter_new_width < MIN_DIMENSION or iter_new_height < MIN_DIMENSION:
                    print(f"Cannot reduce dimensions further below {MIN_DIMENSION}px. Stopping.")
                    break
                print(f"Attempt {i+1}: Resizing to {iter_new_width}x{iter_new_height} (Scale: {current_scale:.2f})")
                image_to_save_this_iteration = current_img.resize((iter_new_width, iter_new_height), Image.Resampling.LANCZOS)
                new_width, new_height = iter_new_width, iter_new_height
            else:
                new_width, new_height = base_width, base_height
            
            try:
                if final_processing_save_format == "JPEG":
                    final_image_for_jpeg = image_to_save_this_iteration
                    if image_to_save_this_iteration.mode == 'RGBA':
                        final_image_for_jpeg = image_to_save_this_iteration.convert('RGB')
                    elif image_to_save_this_iteration.mode == 'P' or image_to_save_this_iteration.mode == 'LA':
                         final_image_for_jpeg = image_to_save_this_iteration.convert('RGB')
                    if final_image_for_jpeg.mode not in ('RGB', 'L'):
                        final_image_for_jpeg = final_image_for_jpeg.convert('RGB')
                    print(f"  Saving as JPEG (Quality: {current_jpeg_quality}).") # Moved print after conversion
                    final_image_for_jpeg.save(temp_buffer, format="JPEG", quality=current_jpeg_quality, optimize=True, progressive=True)
                elif final_processing_save_format == "PNG":
                    print("  Saving as PNG (optimized).")
                    image_to_save_this_iteration.save(temp_buffer, format="PNG", optimize=True)
            except Exception as e_save_loop:
                print(f"Error during save attempt in loop: {e_save_loop}")
                return False, None, None, None, None, None 

            last_attempted_size_bytes = temp_buffer.tell()
            print(f"  Attempt {i+1} -> Size: {last_attempted_size_bytes / 1024:.2f} KB")

            if last_attempted_size_bytes <= TARGET_MAX_BYTES:
                processed_data = temp_buffer.getvalue()
                final_w, final_h = image_to_save_this_iteration.size
                final_size_kb = last_attempted_size_bytes / 1024.0
                
                success_console_msg = (f"Image processed. Format: {final_processing_save_format}, "
                                       f"Size: {final_size_kb:.2f} KB, Dims: {final_w}x{final_h}")
                print(f"\nSuccess! {success_console_msg}")

                if final_w < RECOMMENDED_DIMENSION or final_h < RECOMMENDED_DIMENSION:
                    print(f"Warning: Final dimensions ({final_w}x{final_h}) are below GitHub's recommended {RECOMMENDED_DIMENSION}x{RECOMMENDED_DIMENSION}px.")
                return True, processed_data, final_extension, final_w, final_h, final_size_kb

            if final_processing_save_format == "JPEG" and current_jpeg_quality > JPEG_MIN_QUALITY:
                current_jpeg_quality -= JPEG_QUALITY_STEP
                print(f"  Reducing JPEG quality to: {current_jpeg_quality}") # Added print for clarity
            else:
                current_scale -= DIMENSION_SCALE_STEP
                potential_next_w = int(base_width * current_scale); potential_next_h = int(base_height * current_scale)
                if current_scale < 0.001 or potential_next_w < MIN_DIMENSION or potential_next_h < MIN_DIMENSION :
                    print(f"  Next scale ({current_scale:.2f}) would violate MIN_DIMENSION or is too small. Stopping reduction.") # Added print
                    break 
                print(f"  Reducing scale to: {current_scale:.2f}") # Added print
                if final_processing_save_format == "JPEG":
                    current_jpeg_quality = 85
                    print(f"  Resetting JPEG quality to {current_jpeg_quality} after scaling.") # Added print
        
        print(f"\nFailed to reduce image. Last size: {last_attempted_size_bytes / 1024:.2f} KB.")
        return False, None, None, None, None, None

    except UnidentifiedImageError:
        err_msg = f"Cannot identify image file. '{input_image_path}' may be corrupted or not a supported Pillow type."
        print(f"Error: {err_msg}")
        return False, None, None, None, None, None
    except Exception as e:
        err_msg = f"An unexpected error occurred: {e}"
        print(f"Error: {err_msg}")
        import traceback
        traceback.print_exc()
        return False, None, None, None, None, None

class ImageReducerApp:
    def __init__(self, master):
        self.master = master
        master.title("GitHub Profile Image Reducer")
        self.input_image_path = None
        master.geometry("500x350"); master.configure(bg='#f0f0f0')
        default_font = ("Arial", 10); button_font = ("Arial", 10, "bold")
        main_frame = tk.Frame(master, padx=10, pady=10, bg='#f0f0f0'); main_frame.pack(expand=True, fill=tk.BOTH)
        
        self.select_button = tk.Button(main_frame, text="Select Image", command=self.select_image, font=button_font, bg='#cceeff', width=20)
        self.select_button.pack(pady=(10,5))
        
        self.filepath_label = tk.Label(main_frame, text="No image selected", wraplength=480, bg='#f0f0f0', font=default_font)
        self.filepath_label.pack(pady=5)
        
        self.thumbnail_label = tk.Label(main_frame, bg='#dddddd') # Placeholder for thumbnail
        self.thumbnail_label.pack(pady=10,  fill=tk.BOTH, expand=True) # Allow it to expand
        
        self.process_button = tk.Button(main_frame, text="Process Image", command=self.process_image, state=tk.DISABLED, font=button_font, bg='#ccffcc', width=20)
        self.process_button.pack(pady=5)
        
        self.status_label = tk.Label(main_frame, text="", fg="blue", bg='#f0f0f0', font=default_font)
        self.status_label.pack(pady=(5,10))

    def select_image(self):
        try:
            path = filedialog.askopenfilename(title="Select an image file", filetypes=(("Image files", "*.jpg *.jpeg *.png *.gif"), ("All files", "*.*")))
            if path:
                self.input_image_path = path
                self.filepath_label.config(text=os.path.basename(path))
                self.status_label.config(text=f"Selected: {path}", fg="blue")
                self.process_button.config(state=tk.NORMAL)
                self.display_thumbnail(path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not select image: {e}")
            self.status_label.config(text=f"Error selecting image: {e}", fg="red")

    def display_thumbnail(self, image_path):
        try:
            img = Image.open(image_path)
            # Calculate aspect ratio to fit thumbnail_label without distortion
            # Assuming thumbnail_label has a decent size, e.g., self.thumbnail_label.winfo_width()
            # For simplicity, using a fixed max size for now.
            max_thumb_w, max_thumb_h = 150, 150 # Or get from label size later
            img.thumbnail((max_thumb_w, max_thumb_h), Image.Resampling.LANCZOS)
            
            photo = ImageTk.PhotoImage(img)
            self.thumbnail_label.config(image=photo, text="") # Clear any "Preview N/A" text
            self.thumbnail_label.image = photo 
        except Exception as e:
            self.thumbnail_label.config(image=None, text="Preview N/A")
            self.thumbnail_label.image = None
            print(f"Error creating thumbnail: {e}")

    def process_image(self):
        if not self.input_image_path:
            messagebox.showwarning("No Image", "Please select an image first.")
            return

        self.status_label.config(text="Processing... please wait.", fg="orange")
        self.master.update_idletasks()

        success, image_data, suggested_ext, final_w, final_h, final_size_kb = reduce_image_for_github(self.input_image_path)

        if success and image_data:
            self.status_label.config(text="Processing complete. Choose where to save.", fg="blue")
            
            original_basename = os.path.basename(self.input_image_path)
            original_name_no_ext = os.path.splitext(original_basename)[0]
            suggested_filename = f"{original_name_no_ext}_github{suggested_ext}"

            file_types_map = {".jpg": ("JPEG image", "*.jpg"), ".png": ("PNG image", "*.png")}
            current_file_type = file_types_map.get(suggested_ext, ("All files", "*.*"))
            all_file_types = [current_file_type]
            for ext, desc_pattern in file_types_map.items():
                if ext != suggested_ext:
                    all_file_types.append(desc_pattern)
            if current_file_type[1] != "*.*": # Add "All files" if not already the primary
                 all_file_types.append(("All files", "*.*"))


            save_path = filedialog.asksaveasfilename(
                initialfile=suggested_filename,
                title="Save Processed Image As...",
                defaultextension=suggested_ext,
                filetypes=all_file_types
            )

            if save_path:
                try:
                    with open(save_path, 'wb') as f:
                        f.write(image_data)
                    
                    final_format_str = suggested_ext.upper().replace('.','')
                    success_msg_details = (f"Image saved to:\n{save_path}\n"
                                           f"Final Size: {final_size_kb:.2f} KB\n"
                                           f"Dimensions: {final_w}x{final_h}\n"
                                           f"Format: {final_format_str}")
                    
                    messagebox.showinfo("Success", success_msg_details)
                    self.status_label.config(text="Image saved successfully!", fg="green")
                    if final_w < RECOMMENDED_DIMENSION or final_h < RECOMMENDED_DIMENSION:
                         messagebox.showwarning("Dimension Warning", f"Final dimensions ({final_w}x{final_h}) are below GitHub's recommended {RECOMMENDED_DIMENSION}x{RECOMMENDED_DIMENSION}px.")
                except Exception as e_write:
                    messagebox.showerror("Save Error", f"Could not save file: {e_write}")
                    self.status_label.config(text="Error saving file.", fg="red")
            else:
                self.status_label.config(text="Save cancelled.", fg="blue")
        
        elif success and not image_data:
             messagebox.showerror("Processing Error", "Processing reported success but no image data was returned.")
             self.status_label.config(text="Internal error: No image data.", fg="red")
        else: 
            # If reduce_image_for_github returned False, specific errors are printed to console
            # A generic GUI message is sufficient here unless more detailed error passing is implemented
            messagebox.showerror("Processing Failed", "Image processing failed. See console for details.")
            self.status_label.config(text="Processing failed. Check console.", fg="red")
        
        # Optionally reset GUI for next image
        self.input_image_path = None # Reset after processing
        self.filepath_label.config(text="No image selected")
        self.process_button.config(state=tk.DISABLED)
        self.thumbnail_label.config(image=None, text="") # Clear thumbnail
        self.thumbnail_label.image = None


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageReducerApp(root)
    root.mainloop()