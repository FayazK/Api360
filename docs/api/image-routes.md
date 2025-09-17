# Image Service API Usage

This document provides Postman-compatible `curl` examples for the Image Service endpoints. You can import these examples directly into Postman by using the "Import" -> "Raw Text" feature.

The service provides endpoints for image conversion, batch processing, and AI-powered image generation.

---

## 1. Convert Image

Converts a single image from one format to another, with optional processing.

- **Endpoint**: `POST /api/v1/image/convert`
- **Content-Type**: `multipart/form-data`

### Parameters

- `file` (file, required): The image file to convert.
- `format` (string, optional): Target format (e.g., `jpeg`, `png`, `webp`).
- `width` (integer, optional): Target width in pixels.
- `height` (integer, optional): Target height in pixels.
- `quality` (integer, optional): Compression quality (1-100).
- `lossless` (boolean, optional): Use lossless compression if available (e.g., for WebP).

### Example Request

This example converts an uploaded PNG file to a JPEG, resizing it to a width of 500 pixels with 85% quality.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/image/convert" \
-H "Content-Type: multipart/form-data" \
-F "file=@/path/to/your/image.png" \
-F "format=jpeg" \
-F "width=500" \
-F "quality=85"
```

---

## 2. Batch Convert Images

Converts multiple images using the same conversion settings for all.

- **Endpoint**: `POST /api/v1/image/batch-convert`
- **Content-Type**: `multipart/form-data`

### Parameters

- `files` (list of files, required): The image files to convert (max 20).
- `format`, `width`, etc. (optional): Same as the single `/convert` endpoint, applied to all images.

### Example Request

This example converts two images to the WebP format.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/image/batch-convert" \
-H "Content-Type: multipart/form-data" \
-F "files=@/path/to/your/image1.png" \
-F "files=@/path/to/your/image2.jpg" \
-F "format=webp" \
-F "quality=90"
```

---

## 3. Batch Convert with Individual Options

Converts multiple images, applying a unique set of conversion options to each one.

- **Endpoint**: `POST /api/v1/image/batch-convert-custom`
- **Content-Type**: `multipart/form-data`

### Parameters

- `files` (list of files, required): The image files to convert.
- `items` (string, required): A JSON string representing a list of conversion jobs. Each object in the list must contain:
    - `file_index` (integer): The 0-based index of the file in the `files` list.
    - `conversion_options` (object): An object with the desired conversion options for that specific file (e.g., `format`, `width`, `quality`).

### Example Request

This example converts two images:
1.  The first image (`image1.png`) is converted to PNG, resized to 300px width.
2.  The second image (`image2.jpg`) is converted to JPEG with 75% quality.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/image/batch-convert-custom" \
-H "Content-Type: multipart/form-data" \
-F "files=@/path/to/your/image1.png" \
-F "files=@/path/to/your/image2.jpg" \
-F 'items=[
  {
    "file_index": 0,
    "conversion_options": {
      "format": "png",
      "width": 300
    }
  },
  {
    "file_index": 1,
    "conversion_options": {
      "format": "jpeg",
      "quality": 75
    }
  }
]'
```

---

## 4. Generate or Edit Images (AI)

Generates or edits an image using an AI provider, based on a JSON payload.

- **Endpoint**: `POST /api/v1/image/generate`
- **Content-Type**: `application/json`

### Example Request

This example uses the `replicate` provider with the `bytedance/seedream-4` model to generate an image from a text prompt.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/image/generate" \
-H "Content-Type: application/json" \
-d '{
  "prompt": "A hyper-realistic, cinematic photo of a raccoon wearing a tiny fedora, sitting at a cafe table.",
  "provider": "replicate",
  "model": "bytedance/seedream-4",
  "ratio": "16:9",
  "negative_prompt": "cartoon, drawing, ugly, low quality"
}'
```

---

## 5. Generate or Edit Images (AI) with Multipart Upload

The multipart variant of the AI generation endpoint, allowing for file uploads for image-to-image tasks.

- **Endpoint**: `POST /api/v1/image/generate-multipart`
- **Content-Type**: `multipart/form-data`

### Parameters
- `prompt` (string, required): The main text prompt.
- `provider` (string, optional): The AI provider key.
- `model` (string, optional): The model name for the provider.
- `files` (file, optional): An input image for image-to-image generation.
- `mask` (file, optional): A mask file for inpainting.
- Other parameters (`ratio`, `negative_prompt`, etc.) as form fields.

### Example Request

This example performs an image-to-image task, using an input image to guide the generation.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/image/generate-multipart" \
-H "Content-Type: multipart/form-data" \
-F "prompt=Transform this into a watercolor painting" \
-F "provider=replicate" \
-F "model=bytedance/seedream-4" \
-F "files=@/path/to/your/input_image.jpg" \
-F "ratio=1:1"
```
