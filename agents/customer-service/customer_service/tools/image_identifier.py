import os
import mimetypes
import vertexai
from vertexai.generative_models import GenerativeModel, Part

# Configuration
MODEL_NAME = "gemini-2.0-flash-001" # Reverted to previously used model name
IDENTIFICATION_PROMPT = "Identify the primary plant, vegetable, or gardening tool in this image. Return only the common name of the item. If multiple items are present, identify the most prominent one. If unsure, say 'Unknown'."

def get_mime_type_for_bytes(file_extension_from_filename: str):
    """
    Determines the MIME type from a file extension.
    """
    mime_type, _ = mimetypes.guess_type(f"file.{file_extension_from_filename}")
    if mime_type:
        return mime_type
    # Fallback for common types if guess fails
    ext_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}
    return ext_map.get(file_extension_from_filename.lower())


def identify_item_in_image(image_bytes: bytes, original_filename: str) -> str:
    """
    Identifies the primary item in an image using the Vertex AI Gemini API.

    Args:
        image_bytes: The image data as bytes.
        original_filename: The original filename of the image (to get extension for MIME type).

    Returns:
        A string containing the identified item name, or "Unknown" / error message.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    location = os.environ.get("GOOGLE_CLOUD_LOCATION")

    if not project_id or not location:
        error_msg = "Error: GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION must be set in the environment."
        print(error_msg)
        return error_msg

    file_extension = original_filename.split('.')[-1]
    mime_type = get_mime_type_for_bytes(file_extension)

    if not mime_type or not mime_type.startswith("image/"):
        return f"Error: Invalid or unknown MIME type for file extension '{file_extension}'."

    try:
        # Initialize Vertex AI client. This uses Application Default Credentials.
        vertexai.init(project=project_id, location=location)
        
        # Load the model
        model = GenerativeModel(MODEL_NAME)

        # Prepare the content parts
        image_part = Part.from_data(data=image_bytes, mime_type=mime_type)
        prompt_part = Part.from_text(IDENTIFICATION_PROMPT)
        
        contents = [prompt_part, image_part]

        # Generate content
        response = model.generate_content(contents)

        if response.candidates and response.candidates[0].content.parts:
            identified_item = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text') and part.text)
            return identified_item.strip()
        elif response.prompt_feedback and response.prompt_feedback.block_reason:
            return f"Error: Image analysis blocked - {response.prompt_feedback.block_reason}"
        else:
            return "Unknown (no clear identification from model)"

    except Exception as e:
        print(f"Error during Vertex AI API call in identify_item_in_image: {e}")
        return f"Error: Could not identify item due to API error ({type(e).__name__})."

if __name__ == '__main__':
    # Example usage (for testing this module directly)
    # This section requires Pillow to be installed (pip install Pillow)
    # to create a dummy image if 'test_image.jpg' doesn't exist.
    # The core 'identify_item_in_image' function does NOT require Pillow.

    test_image_path = "test_image.jpg"
    test_filename = "test_image.jpg"
    
    if not os.path.exists(test_image_path):
        print(f"Test image '{test_image_path}' not found. Attempting to create a dummy image for testing this module.")
        try:
            from PIL import Image, ImageDraw # Pillow import for test dummy image only
            img = Image.new('RGB', (100, 30), color = 'red')
            draw = ImageDraw.Draw(img)
            try:
                # Try to add text to make it slightly more than a blank red square
                draw.text((10,10), "Test", fill=(255,255,0))
            except Exception: # Handle cases where font might not be available
                pass
            img.save(test_image_path)
            print(f"Created dummy test image: {test_image_path}")
        except ImportError:
            print("Pillow not installed, cannot create dummy image. Please create test_image.jpg manually.")
            exit()
        except Exception as e:
            print(f"Could not create dummy image: {e}")
            exit()

    if os.path.exists(test_image_path):
        with open(test_image_path, "rb") as f_img:
            img_bytes = f_img.read()
        
        # Ensure your GEMINI_API_KEY is set as an environment variable or in the API_KEY fallback above
        print(f"Attempting to identify item in: {test_filename}")
        result = identify_item_in_image(img_bytes, test_filename)
        print(f"Identification Result: {result}")
    else:
        print(f"Test image '{test_image_path}' not found. Skipping direct test.")