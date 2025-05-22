import os
from PIL import Image, UnidentifiedImageError, ImageFile
import io
import numpy as np # For the test block

# --- Constants ---
TARGET_MAX_BYTES = 0.98 * 1024 * 1024
RECOMMENDED_DIMENSION = 500
MIN_DIMENSION = 200
MAX_ITERATIONS = 15
JPEG_QUALITY_STEP = 7
JPEG_MIN_QUALITY = 60
DIMENSION_SCALE_STEP = 0.1

ImageFile.LOAD_TRUNCATED_IMAGES = True

def reduce_image_for_github(input_image_path, output_image_path_suggestion): # Renamed for clarity
    print(f"Starting reduction for: {input_image_path}")

    if not os.path.exists(input_image_path):
        print(f"Error: Input file not found at '{input_image_path}'")
        return False # Keep return simple: True for success, False for failure

    try:
        img = Image.open(input_image_path)
        original_format = img.format
        original_mode = img.mode
        original_width, original_height = img.size
        initial_size_bytes = os.path.getsize(input_image_path)

        print(f"Image opened:")
        print(f"  Format: {original_format}, Mode: {original_mode}, Dimensions: {original_width}x{original_height}, Size: {initial_size_bytes / 1024:.2f} KB")

        # Determine the base for the output path (directory and name without extension)
        output_dir = os.path.dirname(output_image_path_suggestion)
        output_filename_base = os.path.splitext(os.path.basename(output_image_path_suggestion))[0]
        
        # Ensure output directory exists if it's specified and not current dir
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)


        # Handle images that are already small enough
        if initial_size_bytes <= TARGET_MAX_BYTES:
            print(f"Image already under target size ({TARGET_MAX_BYTES / 1024:.2f} KB). Re-saving for optimization.")
            try:
                current_img_copy = img.copy()
                final_save_format_small = original_format # Tentative
                
                # Determine actual save format for "already small" images
                if original_format == "PNG":
                    final_save_format_small = "PNG"
                    actual_output_path = os.path.join(output_dir, f"{output_filename_base}.png")
                    current_img_copy.save(actual_output_path, format="PNG", optimize=True)
                elif original_format == "JPEG":
                    final_save_format_small = "JPEG"
                    actual_output_path = os.path.join(output_dir, f"{output_filename_base}.jpg")
                    current_img_copy.save(actual_output_path, format="JPEG", quality=95, optimize=True, progressive=True)
                elif original_format == "GIF":
                    final_save_format_small = "PNG" # GIFs become PNGs
                    actual_output_path = os.path.join(output_dir, f"{output_filename_base}.png")
                    current_img_copy.seek(0)
                    if current_img_copy.mode == 'P' and 'transparency' in current_img_copy.info:
                        current_img_copy = current_img_copy.convert("RGBA")
                    elif current_img_copy.mode != 'RGB' and current_img_copy.mode != 'RGBA':
                        current_img_copy = current_img_copy.convert("RGB")
                    current_img_copy.save(actual_output_path, format="PNG", optimize=True)
                else: # Other formats
                    has_alpha_small = current_img_copy.mode in ('RGBA', 'LA') or \
                                   (current_img_copy.mode == 'P' and 'transparency' in current_img_copy.info)
                    if has_alpha_small:
                        final_save_format_small = "PNG"
                        actual_output_path = os.path.join(output_dir, f"{output_filename_base}.png")
                        if current_img_copy.mode != 'RGBA': current_img_copy = current_img_copy.convert("RGBA")
                        current_img_copy.save(actual_output_path, format="PNG", optimize=True)
                    else:
                        final_save_format_small = "JPEG"
                        actual_output_path = os.path.join(output_dir, f"{output_filename_base}.jpg")
                        if current_img_copy.mode != 'RGB': current_img_copy = current_img_copy.convert("RGB")
                        current_img_copy.save(actual_output_path, format="JPEG", quality=95, optimize=True, progressive=True)
                
                final_saved_size = os.path.getsize(actual_output_path)
                print(f"Image re-saved/optimized to '{actual_output_path}'. Final format: {final_save_format_small}, Final size: {final_saved_size / 1024:.2f} KB")
                return True
            except Exception as e_save:
                print(f"Error re-saving already small image: {e_save}.")
                return False # If optimized save fails, report error
        
        print(f"Image needs reduction. Target: < {TARGET_MAX_BYTES / 1024:.2f} KB")

        # --- Prepare image for processing ---
        if original_format == "GIF":
            img.seek(0)
            if img.mode == 'P' and 'transparency' in img.info:
                current_img = Image.new("RGBA", img.size)
                current_img.paste(img)
            elif img.mode == 'RGBA':
                 current_img = img.copy()
            else:
                current_img = img.convert('RGB')
            print("Working with the first frame of the GIF, converted to RGBA/RGB.")
        else:
            current_img = img.copy()

        has_alpha = current_img.mode in ('RGBA', 'LA') or (current_img.mode == 'P' and 'transparency' in current_img.info)
        
        if has_alpha and current_img.mode != 'RGBA':
            current_img = current_img.convert('RGBA')
            print("Converted image to RGBA to preserve transparency.")
        elif not has_alpha and current_img.mode not in ('RGB', 'L'):
            current_img = current_img.convert('RGB')
            print(f"Converted image mode from {original_mode} to RGB.")

        # This is the format we will save in if reduction is successful
        final_processing_save_format = "PNG" if has_alpha else "JPEG"
        print(f"Targeting {final_processing_save_format} format for reduction.")
        
        # Construct the final output path with the correct extension for the reduction case
        actual_output_path_reduced = os.path.join(output_dir, f"{output_filename_base}.{final_processing_save_format.lower()}")


        base_width, base_height = current_img.size
        current_scale = 1.0
        current_jpeg_quality = 90
        last_attempted_size_bytes = initial_size_bytes

        for i in range(MAX_ITERATIONS):
            temp_buffer = io.BytesIO()
            image_to_save_this_iteration = current_img # Start with the mode-converted base image
            
            if current_scale < 1.0:
                new_width = int(base_width * current_scale)
                new_height = int(base_height * current_scale)
                if new_width < MIN_DIMENSION or new_height < MIN_DIMENSION:
                    print(f"Cannot reduce dimensions further below {MIN_DIMENSION}px. Stopping.")
                    break
                print(f"Attempt {i+1}: Resizing to {new_width}x{new_height} (Scale: {current_scale:.2f})")
                image_to_save_this_iteration = current_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            try:
                if final_processing_save_format == "JPEG":
                    final_image_for_jpeg = image_to_save_this_iteration
                    if image_to_save_this_iteration.mode == 'RGBA':
                        print(f"  Converting RGBA to RGB for JPEG (Quality: {current_jpeg_quality}).")
                        final_image_for_jpeg = image_to_save_this_iteration.convert('RGB')
                    elif image_to_save_this_iteration.mode == 'P' or image_to_save_this_iteration.mode == 'LA':
                         print(f"  Converting {image_to_save_this_iteration.mode} to RGB for JPEG (Quality: {current_jpeg_quality}).")
                         final_image_for_jpeg = image_to_save_this_iteration.convert('RGB')
                    else:
                        print(f"  Saving as JPEG (Quality: {current_jpeg_quality}).")
                    final_image_for_jpeg.save(temp_buffer, format="JPEG", quality=current_jpeg_quality, optimize=True, progressive=True)
                elif final_processing_save_format == "PNG":
                    print("  Saving as PNG (optimized).")
                    image_to_save_this_iteration.save(temp_buffer, format="PNG", optimize=True)
            except Exception as e_save_loop:
                print(f"Error during save attempt in loop: {e_save_loop}")
                break

            last_attempted_size_bytes = temp_buffer.tell()
            print(f"  Attempt {i+1} -> Size: {last_attempted_size_bytes / 1024:.2f} KB")

            if last_attempted_size_bytes <= TARGET_MAX_BYTES:
                with open(actual_output_path_reduced, 'wb') as f: # Use correct path
                    f.write(temp_buffer.getvalue())
                final_w, final_h = image_to_save_this_iteration.size
                print(f"\nSuccess! Image saved to '{actual_output_path_reduced}'") # Use correct path
                print(f"  Final Size: {last_attempted_size_bytes / 1024:.2f} KB")
                print(f"  Final Dimensions: {final_w}x{final_h}")
                print(f"  Final Format: {final_processing_save_format}")
                if final_w < RECOMMENDED_DIMENSION or final_h < RECOMMENDED_DIMENSION:
                    print(f"Warning: Final dimensions ({final_w}x{final_h}) are below GitHub's recommended {RECOMMENDED_DIMENSION}x{RECOMMENDED_DIMENSION}px.")
                return True

            if final_processing_save_format == "JPEG" and current_jpeg_quality > JPEG_MIN_QUALITY:
                current_jpeg_quality -= JPEG_QUALITY_STEP
                print(f"  Reducing JPEG quality to: {current_jpeg_quality}")
            else:
                current_scale -= DIMENSION_SCALE_STEP
                if current_scale < (MIN_DIMENSION / max(base_width, base_height, 1)):
                    current_scale = (MIN_DIMENSION / max(base_width, base_height, 1))
                    if current_scale <= 0.01 and not (new_width < MIN_DIMENSION or new_height < MIN_DIMENSION): # check if it's already too small
                         print("  Scale factor critically small. Stopping reduction.")
                         break
                print(f"  Reducing scale to: {current_scale:.2f}")
                if final_processing_save_format == "JPEG":
                    current_jpeg_quality = 85
                    print(f"  Resetting JPEG quality to {current_jpeg_quality} after scaling.")
            
            if current_scale <= 0.01 and not (new_width < MIN_DIMENSION or new_height < MIN_DIMENSION) :
                 print("  Scale factor is critically small. Stopping reduction.")
                 break
        
        print(f"\nFailed to reduce image to target size after {i+1} attempts or min dimension/scale reached.")
        print(f"Last attempted size: {last_attempted_size_bytes / 1024:.2f} KB. Try different input or manual adjustments.")
        return False

    except FileNotFoundError:
        print(f"Error: Input file disappeared: '{input_image_path}'")
        return False
    except UnidentifiedImageError:
        print(f"Error: Cannot identify image file. '{input_image_path}' may be corrupted or not a supported Pillow type.")
        return False
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

# --- Main execution block (for testing) ---
if __name__ == "__main__":
    try:
        # --- Create a TRULY large dummy image for testing reduction path ---
        test_input_file_large = "dummy_large_test_image.png" # Will be saved as .png initially
        width, height = 1200, 1200
        try:
            import numpy as np
            random_data = np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
            img_large = Image.fromarray(random_data, 'RGB')
            print("Created noisy RGB image with numpy.")
        except ImportError:
            print("Numpy not found. Creating a large gradient image instead.")
            img_large = Image.new('RGB', (width, height))
            pixels = img_large.load()
            for i_x in range(width):
                for j_y in range(height):
                    pixels[i_x,j_y] = (i_x % 256, j_y % 256, (i_x+j_y) % 256)
        img_large.save(test_input_file_large, "PNG")
        large_image_size_kb = os.path.getsize(test_input_file_large) / 1024
        print(f"Created dummy large test image: {test_input_file_large}, size: {large_image_size_kb:.2f} KB")

        # The output path suggestion for the large image. The function will adjust the extension.
        # Since input is RGB PNG, it will target JPEG.
        test_output_suggestion_large = "dummy_large_test_image_processed.file" # Extension will be replaced

        success_large = reduce_image_for_github(test_input_file_large, test_output_suggestion_large)
        if success_large:
            print(f"Large image processing function called successfully.")
        else:
            print("Large image processing function encountered an error.")

        # --- Create a small dummy image for testing "already small" path ---
        test_input_file_small = "dummy_small_test_image.jpg"
        img_small = Image.new('RGB', (100, 100), color='blue')
        img_small.save(test_input_file_small, "JPEG", quality=70)
        print(f"\nCreated dummy small test image: {test_input_file_small}, size: {os.path.getsize(test_input_file_small)/1024:.2f} KB")
        
        # Output path suggestion for small image.
        test_output_suggestion_small = "dummy_small_test_image_processed.file" # Extension will be replaced

        success_small = reduce_image_for_github(test_input_file_small, test_output_suggestion_small)
        if success_small:
            print(f"Small image processing function called successfully.")
        else:
            print("Small image processing function encountered an error.")

        # --- Clean up ---
        # More robust cleanup: find processed files by pattern if names are dynamic
        files_to_remove = [test_input_file_large, test_input_file_small]
        # Add processed files to the list (they will now have .jpg or .png extensions)
        # Check for both possible output extensions from our test cases
        processed_large_jpg = os.path.splitext(test_output_suggestion_large)[0] + ".jpg"
        processed_large_png = os.path.splitext(test_output_suggestion_large)[0] + ".png"
        processed_small_jpg = os.path.splitext(test_output_suggestion_small)[0] + ".jpg"
        processed_small_png = os.path.splitext(test_output_suggestion_small)[0] + ".png"
        
        files_to_remove.extend([processed_large_jpg, processed_large_png, processed_small_jpg, processed_small_png])
        
        for f_path in set(files_to_remove): # Use set to avoid trying to remove same file twice
            if os.path.exists(f_path):
                print(f"Cleaning up: {f_path}")
                os.remove(f_path)

    except ImportError as e_imp:
        if 'numpy' in str(e_imp).lower():
            print("Numpy is not installed. Please install it for better large image testing: pip install numpy")
        else:
            print(f"ImportError: {e_imp}. Pillow might not be installed. Please install it: pip install Pillow")
    except Exception as e_main:
        print(f"Error in main block: {e_main}")
        import traceback
        traceback.print_exc()