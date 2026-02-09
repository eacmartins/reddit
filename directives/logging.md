# Directive: Logging Standards

**Goal:** Ensure all execution scripts log their activity to a central log file for auditing and debugging.

**Standards:**
- **Log File:** `logs/execution.log`
- **Format:** `%(asctime)s - %(name)s - %(levelname)s - %(message)s`
- **Levels:**
    - `INFO`: Normal execution steps (start, end, key milestones).
    - `ERROR`: Exceptions and critical failures.
    - `DEBUG`: Detailed data for troubleshooting (optional).

**Implementation:**
- Use Python's built-in `logging` module.
- Configure a `FileHandler` for `logs/execution.log`.
- Configure a `StreamHandler` for stdout (optional, but recommended for user visibility).

**Example Snippet:**
```python
import logging
import os

# Ensure logs dir exists
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/execution.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    logger.info("Script started")
    try:
        # ... logic ...
        logger.info("Script completed successfully")
    except Exception as e:
        logger.error(f"Script failed: {e}")
```
