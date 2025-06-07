import google.genai as genai
from google.genai import types
import os
import mimetypes # For determining MIME type

# --- Configuration ---
# IMPORTANT: Replace with your actual API Key
API_KEY = os.environ.get("GEMINI_API_KEY") 
if not API_KEY:
    # Fallback if environment variable is not set, 
    # but using environment variables is recommended for security.
    API_KEY = "AIzaSyDOS1oFgGoRweAs4rhhvyikDpmjiG1xMlU" # User provided API Key

# Ensure this model name is valid for the API and supports image input
# For Gemini API (ai.google.dev), common vision model is 'gemini-pro-vision' or newer like 'gemini-1.5-flash-latest'
# The model 'gemini-2.0-flash-live-preview-04-09' might be a Vertex AI specific model name
# or an older/experimental one. Using a known working model for Gemini API.
MODEL_NAME = "gemini-2.0-flash-001" # Using model from verified example

IMAGE_PATHS = [
    r"C:\Users\Lenovo\Downloads\Jan_Matejko,_Stańczyk.jpg",
    r"C:\Users\Lenovo\Downloads\bots.jpeg" 
]
TEXT_PROMPT = "Describe this image in detail."
# --- End Configuration ---

def get_mime_type(file_path):
    """Determines the MIME type of a file based on its extension."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".jpg" or ext == ".jpeg":
        return "image/jpeg"
    elif ext == ".png":
        return "image/png"
    elif ext == ".gif":
        return "image/gif"
    elif ext == ".bmp":
        return "image/bmp"
    else:
        print(f"Warning: Could not determine MIME type for {file_path} based on extension. Defaulting to None.")
        return None

def main():
    if not API_KEY or API_KEY == "YOUR_API_KEY_HERE": # Default placeholder check
        print("ERROR: API_KEY is not set. Please set the GEMINI_API_KEY environment variable or update the script.")
        return

    # For Gemini API (ai.google.dev), you directly instantiate GenerativeModel
    # and the API key is usually configured via an environment variable `GOOGLE_API_KEY`
    # or by passing `transport='rest'` and `credentials` to `GenerativeModel` if not using env var.
    # The `genai.configure()` method is not the standard way for the `google-genai` package
    # when using the Gemini API directly (not Vertex AI).
    # The API key is typically picked up from the environment variable GOOGLE_API_KEY.
    # If it's not set, `genai.GenerativeModel` will raise an error.
    # We've already set API_KEY, so we'll ensure it's used if GOOGLE_API_KEY env var isn't set.
    # However, the most straightforward way if API_KEY is in a variable is to use it with `configure`
    # if that were the correct method, or pass it to the model if the model took it.
    # Let's stick to the direct `GenerativeModel` instantiation which relies on `genai.configure`
    # or environment variables.

    # Ensure API_KEY is set for genai.configure if it's to be used.
    # The previous error "module 'google.genai' has no attribute 'configure'"
    # indicates that `genai.configure` is indeed not available directly on the `genai` module.
    # The configuration is typically done when creating a `Client` instance for Vertex AI,
    # or by setting the GOOGLE_API_KEY environment variable for the Gemini API.

    # Given the error, it seems `genai.configure` is not the way for the direct Gemini API.
    # The API key should be set as an environment variable `GOOGLE_API_KEY`.
    # If we must use the API_KEY variable, we might need to use a different initialization
    # or ensure the environment variable is set.

    # Let's assume the environment variable GOOGLE_API_KEY should be set.
    # If not, the GenerativeModel() call will fail.
    # The user has provided API_KEY in the script, so we should try to use that.
    # The `google-generativeai` package (older) used `genai.configure(api_key=...)`.
    # The `google-genai` package (newer, which we are using) for direct Gemini API
    # expects `GOOGLE_API_KEY` env var, or for Vertex AI, a `Client` object.

    # Re-checking documentation for `google-genai` for direct API key usage without Vertex Client.
    # The `google-genai` PyPI page shows:
    # from google import genai
    # client = genai.Client(api_key='GEMINI_API_KEY') # This is for the *Gemini Developer API*
    # And then model = client.models.generate_content(...)
    # OR
    # export GOOGLE_API_KEY='your-api-key'
    # from google import genai
    # model = genai.GenerativeModel(...)

    # The script was trying `genai.configure` which was wrong for `google-genai`.
    # Then it tried `client = genai.Client(api_key=API_KEY)` and `model = client.models.GenerativeModel(MODEL_NAME)`
    # which led to `AttributeError: 'Models' object has no attribute 'GenerativeModel'`.
    # This implies `client.models` does not directly have `GenerativeModel`.

    # Let's try the direct `genai.GenerativeModel` approach, ensuring the API key is set
    # via the environment if `genai.configure` is truly not part of this version of `google-genai`.
    # The PyPI page for `google-genai` (version 1.15.0, close to our 1.14.0)
    # shows `genai.configure(api_key=YOUR_API_KEY)` as a valid way to set the key
    # for the Gemini API (non-Vertex).
    # The error "module 'google.genai' has no attribute 'configure'" is puzzling if the docs are current.
    # Let's assume the docs are correct and there might be an environment issue or a subtle version difference.

    # If `genai.configure` is not found, the alternative is to ensure `os.environ["GOOGLE_API_KEY"] = API_KEY`
    # before `genai.GenerativeModel` is called.

    # Given the persistent `AttributeError: module 'google.genai' has no attribute 'configure'`,
    # it's highly likely that `genai.configure` is NOT the correct method for this version/setup.
    # The most robust way for the Gemini API (non-Vertex) is to set the environment variable.
    # if "GOOGLE_API_KEY" not in os.environ:
    #     os.environ["GOOGLE_API_KEY"] = API_KEY
    #     print(f"Set GOOGLE_API_KEY environment variable from API_KEY in script.")
    # elif os.environ["GOOGLE_API_KEY"] != API_KEY:
    #     print(f"Warning: GOOGLE_API_KEY environment variable is set but differs from API_KEY in script. Using script's API_KEY.")
    #     os.environ["GOOGLE_API_KEY"] = API_KEY

    try:
        # Initialize the client with the API key
        client = genai.Client(api_key=API_KEY)
        print(f"Successfully initialized genai.Client with API_KEY.")
    except Exception as e:
        print(f"Error creating genai.Client: {e}")
        return

    for image_path in IMAGE_PATHS:
        print(f"\n--- Processing image: {image_path} ---")
        if not os.path.exists(image_path):
            print(f"ERROR: Image file not found at {image_path}")
            continue

        mime_type = get_mime_type(image_path)
        if not mime_type:
            print(f"ERROR: Could not determine MIME type for {image_path}. Skipping.")
            continue
        
        print(f"Determined MIME type: {mime_type}")

        try:
            print(f"Reading image file: {image_path}")
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            print(f"Creating image part from bytes with MIME type: {mime_type}")
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            
            contents = [TEXT_PROMPT, image_part] # Order can matter, often text first then image

            print(f"Sending request to model '{MODEL_NAME}' via client.models.generate_content...")
            response = client.models.generate_content(model=MODEL_NAME, contents=contents)

            if response.candidates:
                if response.candidates[0].content and response.candidates[0].content.parts:
                    full_text_response = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text') and part.text)
                    print("\nModel Response:")
                    print(full_text_response)
                else:
                    print("Model response did not contain expected text parts.")
                    print(f"Full candidate: {response.candidates[0]}")

                if hasattr(response, 'prompt_feedback') and response.prompt_feedback and response.prompt_feedback.block_reason:
                    print(f"Prompt was blocked: {response.prompt_feedback.block_reason}")
                    if response.prompt_feedback.safety_ratings:
                        for rating in response.prompt_feedback.safety_ratings:
                            print(rating)
                
                if response.candidates[0].finish_reason != types.FinishReason.STOP:
                     print(f"Generation finished with reason: {response.candidates[0].finish_reason.name}")

            else:
                print("No candidates returned in the response.")
                print(f"Full response: {response}")

        except Exception as e:
            print(f"An error occurred while processing {image_path}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()