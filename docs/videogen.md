# Video Generation Service Implementation Plan

This document outlines the tasks required to implement a new video generation service, mirroring the architecture of the existing image generation service. The initial providers will be Google (VEO) and Replicate.

## 1. Core Architecture & Scaffolding

- [x] **Create Directory Structure:**
  - `app/api/v1/endpoints/video_routes.py`
  - `app/schemas/ai_video.py`
  - `app/services/ai/video/`
  - `app/services/ai/video/drivers/`
  - `app/services/ai/video/drivers/replicate/`
  - `app/services/ai/video/drivers/replicate/models/`
  - `app/services/ai/video/drivers/replicate/schemas/`
  - `app/services/ai/video/persistence.py`
  - `app/services/ai/video/types.py`
  - `app/services/ai/video/factory.py`
  - `app/services/ai/video/base.py`
  - `tests/unit/test_schemas/test_ai_video_schema.py`
  - `tests/unit/test_services/test_video_service.py`

- [x] **Create Configuration File:**
  - Create `config/video_models.yaml` with initial configurations for VEO and Replicate providers.
  ```yaml
  # config/video_models.yaml
  providers:
    - key: "google_veo"
      name: "Google VEO"
      driver: "veo"
      enabled: true
      models:
        - id: "veo-1"
          name: "VEO"
          # Add other model-specific config
    - key: "replicate_video"
      name: "Replicate"
      driver: "replicate"
      enabled: true
      models:
        # Define specific Replicate models here
        - id: "some-replicate-video-model"
          name: "Some Replicate Video Model"
  ```

- [x] **Update Core Config Loading:**
  - Modify `app/core/config.py` to load and parse `config/video_models.yaml`.

## 2. Schemas and Data Models

- [x] **API Schemas (`app/schemas/ai_video.py`):**
  - `VideoGenerationAPIRequest`: Define the request body for the API endpoint. Should include `prompt`, `provider`, `model`, and video-specific parameters like `duration_secs`, `fps`, etc.
  - `VideoGenerationAPIResponse`: Define the response, including `provider`, `model`, `videos` (list of generated videos), and `metadata`.
  - `VideoGenVideo`: Schema for individual video outputs, including `url`, `format`, `size`, etc.

- [x] **Service-Level Types (`app/services/ai/video/types.py`):**
  - `VideoGenerationRequest`: Internal request object used by the `VideoEngine`.
  - `VideoGenerationResult`: Internal result object.
  - `GeneratedVideo`: Internal representation of a single generated video asset.

## 3. Video Service Core

- [x] **Base Driver (`app/services/ai/video/drivers/base_driver.py`):**
  - Create an abstract `BaseVideoDriver` class with a `generate` method that all provider drivers will implement.

- [x] **Video Engine Factory (`app/services/ai/video/factory.py`):**
  - Create a `VideoEngine` class responsible for:
    - Loading video model configurations.
    - Selecting the appropriate driver based on the `provider` in the request.
    - Calling the driver's `generate` method.

- [x] **Video Persistence (`app/services/ai/video/persistence.py`):**
  - Implement `persist_generated_videos` function to save generated videos to public storage (`storage/public/videos/`) and return accessible URLs, similar to the image service.

## 4. Provider Implementation: Google VEO

- [x] **Update Directory Structure:**
  - Add the following directories for VEO model management:
    - `app/services/ai/video/drivers/google/`
    - `app/services/ai/video/drivers/google/models/`
    - `app/services/ai/video/drivers/google/schemas/`

- [x] **VEO Provider Driver (`app/services/ai/video/drivers/google_driver.py`):**
  - Create a main `GoogleVideoDriver` that uses a model registry to delegate to specific VEO version services, similar to the Replicate provider.

- [x] **VEO Model Registry (`app/services/ai/video/drivers/google/registry.py`):**
  - Create a registry to map VEO model IDs (e.g., `veo-2`, `veo-3`) to their corresponding service classes.

- [x] **VEO 2 Model Service (`app/services/ai/video/drivers/google/models/veo2.py`):**
  - Create a dedicated service class for VEO 2.
  - Implement parameter validation and API interaction specific to VEO 2.

- [x] **VEO 3 Model Service (`app/services/ai/video/drivers/google/models/veo3.py`):**
  - Create a dedicated service class for VEO 3.
  - This service must handle a `variation` parameter in the request's `extra` field to distinguish between `veo3` (standard) and `veo3-fast`.
  - Implement logic to call the correct VEO 3 backend based on the `variation`.

- [x] **Update `video_models.yaml`:**
  - Refine the model definitions for Google VEO.
  ```yaml
  # config/video_models.yaml
  providers:
    - key: "google_video"
      name: "Google Video"
      driver: "google" # Points to the main GoogleVideoDriver
      enabled: true
      models:
        - id: "veo-2"
          name: "VEO 2"
        - id: "veo-3"
          name: "VEO 3"
        - id: "veo-3-fast"
          name: "VEO 3 Fast"
  ```

- [x] **Documentation:**
  - Create `docs/sdk/google/veo.md` explaining the different models (`veo-2`, `veo-3`, `veo-3-fast`), their parameters, and how to use the `variation` field for VEO 3.

## 5. Provider Implementation: Replicate

- [x] **Replicate Driver (`app/services/ai/video/drivers/replicate_driver.py`):**
  - Create `ReplicateVideoDriver` that uses a model registry to delegate to model-specific logic.

- [x] **Model Registry (`app/services/ai/video/drivers/replicate/registry.py`):**
  - Create a registry to map Replicate model IDs to their specific driver classes.

- [x] **Model-Specific Drivers (`app/services/ai/video/drivers/replicate/models/`):**
  - For each supported Replicate video model, create a dedicated driver class.
  - Each class will have its own Pydantic schema for validating model-specific `extra` parameters.
  - Example: `app/services/ai/video/drivers/replicate/models/some_model.py`

- [x] **Model-Specific Schemas (`app/services/ai/video/drivers/replicate/schemas/`):**
  - Create JSON schemas for each supported model's parameters, to be used for validation.

- [x] **Documentation:**
  - Create `docs/replicate_video_models.md` detailing supported models and their parameters.

## 6. API Endpoint

- [x] **Create Video Routes (`app/api/v1/endpoints/video_routes.py`):**
  - Create a new router instance.
  - Implement a `POST /generate` endpoint that accepts `VideoGenerationAPIRequest`.
  - Implement a `POST /generate-multipart` endpoint for uploads (e.g., for video-to-video tasks).

- [x] **Integrate into Main App:**
  - Mount the new video router in `app/main.py`.

## 7. Testing

- [x] **Unit Tests:**
  - Write unit tests for the new Pydantic schemas in `test_ai_video_schema.py`.
  - Write unit tests for the `VideoEngine` and provider selection logic in `test_video_service.py`.

- [x] **Integration Tests:**
  - Add integration tests to `tests/integration/test_api_endpoints.py` to test the new `/api/v1/video/generate` endpoint with mock provider responses.

## 8. Documentation

- [x] **Update Main README:**
  - Add a section to the main `README.md` about the new video generation capabilities.
- [x] **Final Review:**
  - Review all new documentation files for clarity and completeness.
