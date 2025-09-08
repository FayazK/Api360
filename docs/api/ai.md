# AI Service API Documentation

This document provides detailed documentation for the AI Service API, which allows for text generation, provider management, and health checks.

The base URL for all endpoints is `/api/v1/ai`.

---

## Endpoints

### 1. Generate Text

Generate text using AI models from various providers. This is the primary endpoint for text generation.

- **URL:** `/generate`
- **Method:** `POST`

#### Request Body

The request body should be a JSON object with the following parameters:

| Parameter            | Type                | Required | Description                                                                                             |
| -------------------- | ------------------- | -------- | ------------------------------------------------------------------------------------------------------- |
| `prompt`             | `string`            | Yes      | The main prompt or a template name to use for generation.                                               |
| `system_prompt`      | `string`            | No       | An optional system-level instruction for the AI model (e.g., "You are a helpful assistant.").           |
| `provider`           | `string`            | No       | The AI provider to use (e.g., "openai", "gemini"). Defaults to the system's default provider if omitted. |
| `model`              | `string`            | No       | The specific model to use (e.g., "gpt-4o", "gemini-1.5-pro"). Defaults to the provider's default model. |
| `max_tokens`         | `integer`           | No       | The maximum number of tokens to generate in the response.                                               |
| `temperature`        | `float`             | No       | Controls randomness (0.0 to 2.0). Higher values mean more creative but less predictable output.         |
| `top_p`              | `float`             | No       | Controls nucleus sampling. The model considers only tokens with a cumulative probability mass of `top_p`.|
| `frequency_penalty`  | `float`             | No       | Penalizes new tokens based on their frequency in the text so far, discouraging repetition.              |
| `presence_penalty`   | `float`             | No       | Penalizes new tokens based on whether they appear in the text so far, encouraging new topics.           |
| `stop_sequences`     | `array of strings`  | No       | A list of sequences at which the model should stop generating text.                                     |
| `template_variables` | `object`            | No       | A dictionary of key-value pairs to substitute in the prompt if it's a template.                         |

#### Success Response (200 OK)

The response is a JSON object containing the generated text and extensive metadata.

| Parameter           | Type      | Description                                                                          |
| ------------------- | --------- | ------------------------------------------------------------------------------------ |
| `text`              | `string`  | The generated text.                                                                  |
| `success`           | `boolean` | `true` if the generation was successful.                                             |
| `provider`          | `string`  | The AI provider that was used.                                                       |
| `model`             | `string`  | The specific model that was used.                                                    |
| `request_id`        | `string`  | A unique identifier for the request, provided by the AI provider.                    |
| `created_at`        | `string`  | The timestamp (UTC) when the request was processed.                                  |
| `response_time_ms`  | `float`   | The time taken to generate the response, in milliseconds.                            |
| `prompt_tokens`     | `integer` | The number of tokens in the input prompt.                                            |
| `completion_tokens` | `integer` | The number of tokens in the generated text.                                          |
| `total_tokens`      | `integer` | The total number of tokens used (`prompt_tokens` + `completion_tokens`).             |
| `cost_usd`          | `float`   | The estimated cost of the API call in USD.                                           |
| `finish_reason`     | `string`  | The reason the model stopped generating text (e.g., "stop", "length").               |
| `parameters`        | `object`  | The parameters that were used for the generation request.                            |
| `error`             | `object`  | An object containing error details if `success` is `false`.                          |

#### Error Responses

- **400 Bad Request:** The request was malformed or failed due to an issue with the provider (e.g., content moderation).
- **422 Unprocessable Entity:** The request body has validation errors (e.g., incorrect data types).
- **500 Internal Server Error:** An unexpected error occurred on the server.
- **503 Service Unavailable:** The AI service or all its providers are currently unavailable.

#### Usage Examples

**1. Basic Text Generation**

This example sends a simple prompt and uses the system's default provider and model.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ai/generate" \
-H "Content-Type: application/json" \
-d \
'{
  "prompt": "Write a short story about a robot who discovers music."
}'
```

**2. Specifying Provider, Model, and Parameters**

This example uses OpenAI's `gpt-4o` model with a specific temperature and token limit.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ai/generate" \
-H "Content-Type: application/json" \
-d \
'{
  "prompt": "Explain the theory of relativity in simple terms.",
  "provider": "openai",
  "model": "gpt-4o",
  "max_tokens": 150,
  "temperature": 0.7
}'
```

**3. Using a Prompt Template**

This example uses a prompt template named `product_description` (assuming it exists on the server) and provides variables to fill it in.

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ai/generate" \
-H "Content-Type: application/json" \
-d \
'{
  "prompt": "product_description",
  "template_variables": {
    "product_name": "Quantum Coffee Mug",
    "features": ["Self-heating", "Unspillable", "Connects to WiFi"]
  }
}'
```

---

### 2. Get Available Providers

Retrieve information about the available AI providers, their models, and health status.

- **URL:** `/providers`
- **Method:** `GET`

#### Success Response (200 OK)

Returns a JSON object with details about configured and available providers.

| Parameter              | Type     | Description                                                              |
| ---------------------- | -------- | ------------------------------------------------------------------------ |
| `providers`            | `object` | A dictionary where keys are provider names and values are their details. |
| `default_provider`     | `string` | The default provider configured for the system.                          |
| `configured_providers` | `array`  | A list of provider names that have API keys configured.                  |

Each object within `providers` contains:
- `healthy`: `boolean`
- `models`: `array of strings`
- `default_model`: `string`
- `last_checked`: `string` (timestamp)

#### Usage Example

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/ai/providers"
```

---

### 3. Health Check

Check the overall health of the AI service and the status of each configured provider.

- **URL:** `/health`
- **Method:** `GET`

#### Success Response (200 OK)

Returns a JSON object summarizing the health status.

| Parameter    | Type      | Description                                                                                             |
| ------------ | --------- | ------------------------------------------------------------------------------------------------------- |
| `healthy`    | `boolean` | `true` if at least one provider is operational.                                                         |
| `providers`  | `object`  | A dictionary mapping provider names to their health status (`true` or `false`).                         |
| `configured` | `boolean` | `true` if at least one provider has its API key set in the environment.                                 |
| `message`    | `string`  | A summary message of the overall health status.                                                         |

#### Usage Example

```bash
curl -X GET "http://127.0.0.1:8000/api/v1/ai/health"
```

---

### 4. Validate Request

Validate a text generation request without executing it. This is useful for checking parameters and estimating costs before making a real request.

- **URL:** `/validate`
- **Method:** `POST`

#### Request Body

The request body is identical to the `/generate` endpoint.

#### Success Response (200 OK)

Returns a JSON object indicating if the request is valid.

| Parameter  | Type      | Description                                                              | 
| ---------- | --------- | ------------------------------------------------------------------------ |
| `valid`    | `boolean` | `true` if the request is valid and can be processed.                     |
| `provider` | `string`  | The provider that would be used for this request.                        |
| `model`    | `string`  | The model that would be used for this request.                           |
| `message`  | `string`  | A confirmation or error message.                                         |

#### Error Response (400 Bad Request)

If validation fails, the response will have `valid: false` and a descriptive message.

#### Usage Example

```bash
curl -X POST "http://127.0.0.1:8000/api/v1/ai/validate" \
-H "Content-Type: application/json" \
-d \
'{
  "prompt": "This is a test prompt.",
  "provider": "openai",
  "model": "gpt-4o",
  "max_tokens": -100 
}'
```

This would fail validation due to the negative `max_tokens` value.

