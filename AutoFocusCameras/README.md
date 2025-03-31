# Rhombus Auto-Focus Script

This Python script checks the focus quality of Rhombus cameras using AI analysis and triggers the camera's auto-focus mechanism if an image is detected as blurry. It supports multiple AI models (GPT-4o mini, Google Gemini, Claude Haiku) for image analysis and generates a report for cameras that remain blurry after an auto-focus attempt, requiring manual intervention.

## Features

*   Fetches camera lists and image frames from the Rhombus API.
*   Analyzes image blurriness using selected AI models (OpenAI, Gemini, or Claude).
*   Rates image sharpness on a 1-4 scale (1=Severely Blurry, 4=Excellent Focus).
*   Triggers the Rhombus camera's built-in autofocus mechanism for blurry cameras.
*   Re-evaluates camera focus after a waiting period post-refocus trigger.
*   Saves analyzed images locally in an `camera_images` directory, marked as `[BLURRY]` or `[CLEAR]`.
*   Generates a detailed text report (`human_attention_report_*.txt`) listing cameras that failed to refocus or encountered errors.
*   Supports processing cameras across all locations or targeting specific location UUIDs.
*   Provides estimated API cost tracking for the AI analysis.
*   Includes an option to clean up downloaded images after execution.

## Prerequisites

*   Python 3.x
*   Required Python packages: `requests`, `tiktoken`, `urllib3`
*   API Keys:
    *   Rhombus API Key
    *   OpenAI API Key (if using `openai` model)
    *   Google AI Studio API Key (if using `gemini` model)
    *   Anthropic API Key (if using `claude` model)

## Setup

1.  **Install Dependencies:**
    ```bash
    pip3 install -r /path/to/requirements.txt
    ```

2.  **Configure API Keys:**
    Open the `FocusRhombusCameras.py` script and replace the placeholder API keys near the top of the file with your actual keys:
    ```python
    RHOMBUS_API_KEY = "YOUR_RHOMBUS_KEY"  # Replace with Rhombus API key
    OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"    # Replace with OpenAI API key
    GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"      # Replace with Google AI Studio API Key
    ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY" # Replace with Anthropic API Key
    ```
    *Ensure you provide the correct key for the AI model you intend to use.*

## Usage

Run the script from your terminal.

```bash
python3 FocusRhombusCameras.py [options]
```

**Options:**

*   `-model <model_name>`: Specify the AI model for analysis.
    *   Choices: `openai` (default), `gemini`, `claude`
    *   Example: `python FocusRhombusCameras.py -model gemini`
*   `-location <UUID>`: Process only cameras in the specified location UUID. Can be used multiple times for multiple locations.
    *   Example: `python FocusRhombusCameras.py -location uuid_123 -location uuid_456`
*   `-all`: Explicitly process cameras in all locations (**this is the default behavior if `-location` is not specified**).
    *   Example: `python FocusRhombusCameras.py -all`
*   `-clean`: Remove the `camera_images` directory and its contents after the script finishes.
    *   Example: `python FocusRhombusCameras.py -clean`

**Examples:**

*   Check all cameras using the default OpenAI model:
    ```bash
    python3 FocusRhombusCameras.py
    ```
*   Check cameras in two specific locations using the Claude model and clean up images afterwards:
    ```bash
    python3 FocusRhombusCameras.py -model claude -location LOC_UUID_1 -location LOC_UUID_2 -clean
    ```

## Cost Considerations

This script utilizes paid AI APIs for image analysis. Costs vary depending on the model chosen (`openai`, `gemini`, `claude`). The script provides a rough *estimated* cost summary at the end of execution based on the number of images analyzed and the approximate token counts. 
Refer to the pricing pages of OpenAI, Google Cloud (Vertex AI/AI Studio), and Anthropic for detailed and up-to-date cost information.

## Notes
*   **Default Behavior** Processes **ALL** locations if not specified and defaults to OpenAI's GPT-4o Mini.
*   **Blurriness Threshold:** By default (`BLURRINESS_THRESHOLD = 2`), cameras receiving a blur rating of 1 or 2 from the AI will trigger the refocus process.
*   **Refocus Wait Time:** The script waits for `REFOCUS_WAIT_TIME` (default: 60 seconds) after triggering autofocus before re-checking the camera.
*   **R600 Cameras:** Triggering autofocus might require specifying the video stream (`v#`) in the `update_camera_autofocus` function payload for R600 models, as noted in the script's comments. The current default (`v0`) might need adjustment depending on your setup.
*   **Federated Session Tokens:** The script uses Rhombus federated session tokens for efficient image downloading.
*   **Error Handling:** The script attempts to handle common API errors and connection issues, logging them appropriately. Cameras encountering persistent errors during the process might be added to the human attention report.


