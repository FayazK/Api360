# Developer Guide: Implementing Google's Veo Models with the Gemini API

This guide provides a comprehensive, up-to-date walkthrough for developers on how to use Google's Veo video generation models using the official Gemini API Python SDK.

**Source:** [Official Google AI for Developers Documentation](https://ai.google.dev/gemini-api/docs/video)
**Last Updated:** September 2025

## 1. Veo Models: Overview and Capabilities

Veo is a family of generative video models. Veo 3 is the flagship, capable of generating high-fidelity videos with natively generated audio, while Veo 2 is an earlier model for silent videos.

### Model Comparison

| Feature            | Veo 3 (`veo-3.0-generate-001`) | Veo 3 Fast (`veo-3.0-fast-generate-001`) | Veo 2 (`veo-2.0-generate-001`) |
|:-------------------|:-------------------------------|:-----------------------------------------|:-------------------------------|
| **Use Case**       | Highest quality generation     | Speed and cost-efficiency                | General purpose silent video   |
| **Output Audio**   | **Yes (Native)**               | **Yes (Native)**                         | No (Silent only)               |
| **Resolution**     | 720p, 1080p                    | 720p, 1080p                              | 720p only                      |
| **Video Duration** | 8 seconds                      | 8 seconds                                | 5-8 seconds                    |
| **Inputs**         | Text, Image                    | Text, Image                              | Text, Image                    |
| **Output Videos**  | 1 per request                  | 1 per request                            | Up to 2 per request            |
| **Frame Rate**     | 24 FPS                         | 24 FPS                                   | 24 FPS                         |

## 2. Prerequisites & Setup

1.  **Google Cloud Project:** Ensure you have a Google Cloud account and a project with billing enabled.
2.  **Authentication:** Authenticate your local environment with the gcloud CLI.
    ```bash
    gcloud auth application-default login
    ```
3.  **Installation:** Install the official Google AI Python SDK.
    ```bash
    pip install -q google-generativeai
    ```

## 3. Implementation: Text-to-Video with Veo 3

This example shows how to generate a video with audio from a text prompt and customize it with a negative prompt.

```python
import time
import os
from google import genai
from google.genai import types

# --- 1. Configuration ---
# This client uses your Application Default Credentials for authentication.
client = genai.Client()

# Ensure the output directory exists
os.makedirs("generated_videos", exist_ok=True)

# --- 2. Define Prompt and Parameters ---
prompt = "A cinematic, dramatic shot of a majestic lion in the savannah at sunset."
negative_prompt = "cartoon, drawing, low quality, unrealistic"

# --- 3. Submit the Asynchronous Generation Job ---
print("Submitting video generation job...")
operation = client.models.generate_videos(
    model="veo-3.0-generate-001",
    prompt=prompt,
    config=types.GenerateVideosConfig(negative_prompt=negative_prompt),
)

# --- 4. Poll for Completion ---
print("Job submitted. Polling for completion...")
while not operation.done:
    print("Status: In progress... waiting 10 seconds.")
    time.sleep(10)
    # Refresh the operation object to get the latest status.
    operation = client.operations.get(operation)

# --- 5. Download the Video ---
print("Job completed. Downloading video...")
try:
    video = operation.response.generated_videos[0]
    client.files.download(file=video.video)

    output_filename = f"generated_videos/veo3_video_{int(time.time())}.mp4"
    video.video.save(output_filename)
    print(f"✅ Generated video saved to {output_filename}")

except Exception as e:
    print(f"❌ Error downloading video: {e}")

```

## 4. Implementation: Image-to-Video Workflow

A powerful workflow is to first generate a high-quality image with a model like Imagen, and then use that image as the starting point for your video.

```python
import time
import os
from google import genai

# --- 1. Configuration ---
client = genai.Client()
os.makedirs("generated_videos", exist_ok=True)

prompt = "Panning wide shot of a calico kitten sleeping in the sunshine on a windowsill."

# --- 2. Generate an Image with Imagen ---
print("Step 1: Generating an image with Imagen...")
imagen = client.models.generate_images(
    model="imagen-4.0-generate-001", # Assumes access to Imagen 4
    prompt=prompt,
)
start_image = imagen.generated_images[0].image
print("Image generated successfully.")

# --- 3. Generate Video with Veo 3 Using the Image ---
print("Step 2: Submitting video generation job with the image...")
operation = client.models.generate_videos(
    model="veo-3.0-generate-001",
    prompt=prompt,
    image=start_image,
)

# --- 4. Poll for Completion ---
print("Job submitted. Polling for completion...")
while not operation.done:
    print("Status: In progress... waiting 10 seconds.")
    time.sleep(10)
    operation = client.operations.get(operation)

# --- 5. Download the Video ---
print("Job completed. Downloading video...")
video = operation.response.generated_videos[0]
client.files.download(file=video.video)

output_filename = f"generated_videos/veo3_from_image_{int(time.time())}.mp4"
video.video.save(output_filename)
print(f"✅ Generated video saved to {output_filename}")
```

## 5. Important Considerations

-   **Asynchronous Operations:** Video generation is not instant. It returns an `operation` object that you must poll until completion.
-   **Video Retention:** Generated videos are **only stored for 2 days**. You must download them within this period.
-   **Watermarking:** All generated videos are watermarked with SynthID to identify them as AI-generated.
-   **Regional Restrictions:** The `personGeneration` parameter has specific restrictions in certain regions (EU, UK, etc.). Refer to the official documentation for details.
-   **Safety Filters:** All prompts and generated videos are subject to safety filters. If content is blocked, you will not be charged.

