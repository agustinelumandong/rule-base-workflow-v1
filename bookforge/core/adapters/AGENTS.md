# BookForge Adapters Developer Instructions

Use these rules when modifying third-party service integration wrappers or communication layers under `bookforge/core/adapters/`.

---

## 1. Third-Party Service Decoupling
- **Interfaces & Protocols**: Always declare abstract interfaces or Python typing protocols for external API adaptions. The core domain should not depend directly on concrete service instances.
- **Robust Mocking**: Ensure every adapter can be mocked locally inside unit tests without making actual network requests.

---

## 2. Zero-Dependency Fallbacks (`compression.py`)
- When depending on optional libraries (e.g., `headroom` or other proprietary compression extensions):
  1. Wrap the import in a `try-except ImportError` block.
  2. Implement a local, pure-Python fallback (such as `LocalRegexBackend`) that mimics the expected compression behavior.
  3. Log a warning about missing library integrations rather than raising a system-wide exception.

---

## 3. Network & API Error Resilience
- Wrap all network-bound requests in retry handlers.
- Handle common errors (timeouts, rate-limiting, status errors) gracefully, returning clean, type-hinted results (such as an empty list or dictionary) to the core orchestrators instead of crashing the process.
