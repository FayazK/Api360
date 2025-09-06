# Project Architectural and Organizational Issues

This document outlines the architectural, organizational, and pattern-related issues found during a review of the project.

## Architectural Issues

1.  **Monolithic Structure:** The project combines several unrelated services (AI, charts, PDF, image processing) into a single application. This monolithic approach can lead to:
    *   **High Coupling:** Changes in one service might unintentionally affect others.
    *   **Scalability Challenges:** It's difficult to scale individual services based on their specific needs. For example, the AI service might require more resources than the chart service.
    *   **Maintenance Overhead:** The codebase can become complex and hard to manage as it grows.
    *   **Recommendation:** Consider breaking down the application into smaller, independent microservices for each domain (e.g., an `AIService`, a `ChartService`, etc.). This would improve modularity, scalability, and maintainability.

2.  **Lack of a Service Layer in `chart_routes`:** The `chart_routes.py` file directly calls `create_chart`, which in turn calls `save_svg`. This violates the principle of separation of concerns.
    *   **Recommendation:** The `chart_service.py` should be responsible for the business logic of creating the chart, while the route handles the HTTP request and response. The service should not be responsible for saving the file. Instead, it should return the chart data, and the route or a dedicated file-handling service should manage saving it.

3.  **Inconsistent Abstraction in AI Service:**
    *   The `BaseAITextGenerator` provides a good abstraction for different AI providers.
    *   However, the `OpenAIDriver` contains pricing information, which is a business-level concern. This information should be moved to a separate configuration or a pricing service to keep the driver focused on interacting with the OpenAI API.
    *   **Recommendation:** Decouple pricing logic from the driver.

## Organizational Issues

1.  **Configuration Management:**
    *   The AI service relies on `settings.AI_DEFAULT_PROVIDER`, `settings.AI_MAX_TOKENS_DEFAULT`, etc. While using a central configuration object is good, it's not ideal for a service to be so tightly coupled to the global settings.
    *   **Recommendation:** Inject configuration into services and drivers through their constructors. This improves testability and makes the components more reusable.

2.  **Hardcoded Values:**
    *   The `OpenAIDriver` has hardcoded model names and pricing. This makes it difficult to update without changing the code.
    *   **Recommendation:** Externalize this information into a configuration file (e.g., a YAML or JSON file) that can be loaded at runtime.

3.  **Missing `__init__.py` in `app/services/ai/drivers`:** The `drivers` directory is missing an `__init__.py` file, which can cause issues with packaging and imports.
    *   **Recommendation:** Add an empty `__init__.py` file to the `app/services/ai/drivers` directory.

## Patterns and Principles

1.  **Dependency Injection:**
    *   The AI service uses a factory pattern (`AITextGeneratorFactory`) to create and manage the service instance, which is good.
    *   However, the `get_ai_service` dependency in `ai_routes.py` is a bit of a "service locator" pattern, which can hide dependencies and make testing harder.
    *   **Recommendation:** Use a proper dependency injection framework (like `fastapi-injector` or `punq`) to manage dependencies more explicitly. This would make the application more modular and easier to test.

2.  **Single Responsibility Principle (SRP):**
    *   The `chart_service.py` violates SRP by being responsible for both creating the chart and saving it.
    *   The `OpenAIDriver` violates SRP by being responsible for both API interaction and pricing calculation.
    *   **Recommendation:** Refactor these components to have a single, well-defined responsibility.

3.  **Error Handling:**
    *   The error handling in `ai_routes.py` is extensive and well-structured, with custom exceptions. This is a good practice.
    *   However, the `chart_routes.py` has no explicit error handling.
    *   **Recommendation:** Add robust error handling to all routes and services to ensure the application is resilient.
