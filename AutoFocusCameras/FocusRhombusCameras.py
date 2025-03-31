###################################################################################
# Copyright (c) 2025 Rhombus Systems                                              #
#                                                                                 #
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 #
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################

import requests
import time
import base64
import os
import tiktoken
import argparse
from datetime import datetime
import shutil
import urllib3
import re
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# MUST REPLACE THESE VALUES
RHOMBUS_API_KEY = "YOUR_RHOMBUS_KEY"  # Replace with Rhombus API key
OPENAI_API_KEY = "YOUR_OPENAI_API_KEY"    # Replace with OpenAI API key
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY"      # Replace with Google AI Studio API Key
ANTHROPIC_API_KEY = "YOUR_ANTHROPIC_API_KEY" # Replace with Anthropic API Key


# API endpoints
RHOMBUS_BASE_URL = "https://api2.rhombussystems.com/api"
API_ENDPOINTS = {
    "openai": "https://api.openai.com/v1/chat/completions",
    "gemini": f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}",
    "claude": "https://api.anthropic.com/v1/messages"
}
MODEL_NAMES = {
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
    "claude": "claude-3-haiku-20240307"
}


# Constants
BLURRINESS_THRESHOLD = 2  # Trigger auto-focus if blur rating is 2 or lower [1 - terrible \ 4 - best]
REFOCUS_WAIT_TIME = 60   # Wait 60 seconds for camera to refocus


MODEL_COSTS = {
    "openai": {
        "image_cost": 0.00255,
        "cost_per_1k_output_tokens": 0.015
    },
    "gemini": {
        "image_cost": 0.00025,
        "cost_per_1k_output_tokens": 0.0005
    },
    "claude": {
        "image_cost": 0.00125,
        "cost_per_1k_output_tokens": 0.00125
    }
}


IMAGE_DIR = "camera_images"


def log(message, level="INFO", camera_name=None, camera_uuid=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Add camera uuid if provided
    if camera_name:
        if camera_uuid:
            device_info = f"[{camera_name} ({camera_uuid[:8]}...)]"
        else:
            device_info = f"[{camera_name}]"
        print(f"[{level}] {timestamp} {device_info} - {message}")
    else:
        print(f"[{level}] {timestamp} - {message}")

def count_tokens(text, model_name="openai"):
    """Count the number of tokens in a text string using model-specific methods"""
    if model_name == "openai":
        try:
            encoding = tiktoken.get_encoding("cl100k_base")
            return len(encoding.encode(text))
        except Exception as e:
            log(f"Tiktoken encoding failed: {e}. Falling back to approximation.", "WARNING")
            return len(text) // 4
    else:
        return len(text) // 4

def calculate_cost(prompt_tokens, response_text, model_name):
    """Calculate the cost of an API call based on the model used"""
    if model_name not in MODEL_COSTS:
        log(f"Unknown model '{model_name}' for cost calculation. Returning zero cost.", "ERROR")
        return {
            "image_cost": 0,
            "output_tokens": 0,
            "output_cost": 0,
            "total_cost": 0
        }

    costs = MODEL_COSTS[model_name]
    image_cost = costs.get("image_cost", 0)

    output_tokens = count_tokens(response_text, model_name)
    cost_per_1k_output = costs.get("cost_per_1k_output_tokens", 0)
    output_cost = (output_tokens / 1000) * cost_per_1k_output

    return {
        "image_cost": image_cost,
        "output_tokens": output_tokens,
        "output_cost": output_cost,
        "total_cost": image_cost + output_cost
    }

def get_all_cameras():
    """Get a list of all cameras and their status"""
    url = f"{RHOMBUS_BASE_URL}/camera/getMinimalCameraStateList"
    headers = {
        "Content-Type": "application/json",
        "x-auth-scheme": "api-token",
        "x-auth-apikey": RHOMBUS_API_KEY
    }
    
    try:
        response = requests.post(url, headers=headers)
        response.raise_for_status()
        return response.json()["cameraStates"]
    except Exception as e:
        log(f"Error retrieving camera list: {str(e)}", "ERROR")
        return []

def get_frame_uri(camera_uuid, timestamp_ms=None):
    """Get the URI for a specific camera frame"""
    url = f"{RHOMBUS_BASE_URL}/video/getExactFrameUri"
    headers = {
        "Content-Type": "application/json",
        "x-auth-scheme": "api-token",
        "x-auth-apikey": RHOMBUS_API_KEY
    }
    
    # MUST BE IN UNIX MS
    if timestamp_ms is None:
        timestamp_ms = int(time.time() * 1000)
    
    payload = {
        "cameraUuid": camera_uuid,
        "timestampMs": timestamp_ms
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        if result.get("error", True):
            log(f"Error retrieving frame URI: {result.get('responseMessage', 'Unknown error')}", "ERROR")
            return None
        return result.get("frameUri")
    except Exception as e:
        log(f"Error retrieving frame URI: {str(e)}", "ERROR")
        return None

def download_images_with_shared_token(image_urls):
    """Download images using the federated session token"""
    downloaded_images = {}
    
    try:
        session = requests.session()
        session.verify = False
        
        
        session.headers.update({
            "Content-Type": "application/json",
            "x-auth-scheme": "api-token",
            "x-auth-apikey": RHOMBUS_API_KEY
        })
        
        token_req_payload = {"durationSec": 7200}  # 2 hours to ensure it doesn't expire
        token_resp = session.post(
            f"{RHOMBUS_BASE_URL}/org/generateFederatedSessionToken",
            json=token_req_payload
        )
        
        if token_resp.status_code != 200:
            log(f"Failed to retrieve federated session token: {token_resp.content}", "ERROR")
            return downloaded_images
            
        federated_session_token = token_resp.json()["federatedSessionToken"]
        log(f"Successfully generated federated session token")
        
        # Set the cookie for all future requests in this session
        cookie = {"RSESSIONID": f"RFT:{federated_session_token}"}
        session_cookie = requests.cookies.cookiejar_from_dict(cookie)
        session.cookies.update(session_cookie)
        
        # Also set it as a header in case cookies aren't being properly passed
        session.headers.update({"Cookie": f"RSESSIONID=RFT:{federated_session_token}"})
        
        
        for i, image_url in enumerate(image_urls):
            log(f"Downloading image {i+1}/{len(image_urls)}...")
            
            try:
                
                image_resp = session.get(image_url)
                image_resp.raise_for_status()
                
                # Verify it's actually an image
                content_type = image_resp.headers.get('Content-Type', '')
                if 'image' in content_type.lower():
                    image_data = image_resp.content
                    downloaded_images[image_url] = image_data
                    log(f"Successfully downloaded image ({len(image_data)} bytes)", camera_name=None, camera_uuid=None)
                else:
                    log(f"Downloaded content is not an image. Content-Type: {content_type}", "ERROR")
            except Exception as e:
                log(f"Error downloading image: {str(e)}", "ERROR")
            log("==================================================================")
            # Add a short delay between downloads - to not get rate limited
            if i < len(image_urls) - 1:
                time.sleep(1)
                
    except Exception as e:
        log(f"Error in shared token download process: {str(e)}", "ERROR")
        
    return downloaded_images

def update_camera_autofocus(camera_uuid, enable=True):
    """Update the camera's autofocus settings"""
    url = f"{RHOMBUS_BASE_URL}/deviceconfig/updateFacetedConfig"
    headers = {
        "Content-Type": "application/json",
        "x-auth-scheme": "api-token",
        "x-auth-apikey": RHOMBUS_API_KEY
    }
    
    ### NOTE : 
    # this will not work with R600s unless the 'v#' stream is specified below 
    payload = {
        "configUpdate": {
            "videoFacetSettings": {
                "v0": {
                    "motor_config": {
                        "af_enabled": enable
                    }
                }
            },
            "deviceUuid": camera_uuid
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        if result.get("error", True):
            log(f"Error updating camera autofocus: {result.get('responseMessage', 'Unknown error')}", "ERROR")
            return False
        return True
    except Exception as e:
        log(f"Error updating camera autofocus: {str(e)}", "ERROR")
        return False

def trigger_camera_refocus(camera_uuid, camera_name=None):
    """Trigger camera refocus by disabling and re-enabling autofocus"""
    log(f"Triggering refocus", "INFO", camera_name, camera_uuid)
    
    if not update_camera_autofocus(camera_uuid, enable=False):
        log(f"Failed to disable autofocus", "ERROR", camera_name, camera_uuid)
        return False
    # Dependant on camera model this can take longer than 15 Seconds
    log("Waiting 15 seconds before re-enabling autofocus...", "INFO", camera_name, camera_uuid)
    time.sleep(15)
    
    # Re-enable autofocus
    if not update_camera_autofocus(camera_uuid, enable=True):
        log(f"Failed to re-enable autofocus", "ERROR", camera_name, camera_uuid)
        return False
    
    log(f"Successfully triggered refocus", "INFO", camera_name, camera_uuid)
    return True

def analyze_image_blurriness(image_data, model_name, camera_name=None, camera_uuid=None):
    """Analyze image blurriness using the specified AI model"""
    if not image_data:
        log("No image data provided for blurriness analysis", "ERROR", camera_name, camera_uuid)
        return None, None, calculate_cost(0, "", model_name)

    if model_name not in API_ENDPOINTS:
        log(f"Invalid model name specified: {model_name}", "ERROR", camera_name, camera_uuid)
        return None, None, calculate_cost(0, "", model_name)

    api_url = API_ENDPOINTS[model_name]
    model_identifier = MODEL_NAMES[model_name]

    headers = {"Content-Type": "application/json"}
    payload = {}
    ### In terms of a numeric scale, 
    # 1-4 yielded the most consistent results 
    prompt_text = """Rate the overall sharpness/focus of this ENTIRE image using the 4-point scale below:

    4 = Excellent: Tack sharp focus on the intended subject(s). Crisp details, high clarity.
    3 = Acceptable/Good: Mostly sharp and clear. May have minor softness or small out-of-focus areas, but the overall impression is sufficiently clear for the image's likely purpose.
    2 = Poor/Borderline Unacceptable: Significantly blurry or soft. Key elements might be recognizable, but the lack of focus noticeably detracts from the image and limits its usability. Details are largely lost.
    1 = Unacceptable/Severe Blur: Subjects are very poorly defined or unrecognizable. Details are completely lost. Unusable due to focus issues.

    Instructions:
    - Assess the focus across the ENTIRE image frame.
    - Be critical when deciding between '2' (Poor) and '3' (Acceptable/Good). Does the blur *significantly* impair the image?

    Provide your rating as a single number followed by a very short explanation in this format: "Rating: X - Explanation"
    """

    # Encode image as base64
    base64_image = base64.b64encode(image_data).decode('utf-8')

    try:
        if model_name == "openai":
            headers["Authorization"] = f"Bearer {OPENAI_API_KEY}"
            payload = {
                "model": model_identifier,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt_text},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                 "max_tokens": 100
            }
        elif model_name == "gemini":
            payload = {
                "contents": [{
                    "parts": [
                        {"text": prompt_text},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": base64_image
                            }
                        }
                    ]
                }],
                "generationConfig": {
                    "maxOutputTokens": 100
                }
            }
        elif model_name == "claude":
            headers["x-api-key"] = ANTHROPIC_API_KEY
            headers["anthropic-version"] = "2023-06-01"
            payload = {
                "model": model_identifier,
                "max_tokens": 100,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": base64_image,
                                }
                            },
                            {"type": "text", "text": prompt_text}
                        ]
                    }
                ]
            }
        else:
            raise ValueError(f"Model configuration not implemented for: {model_name}")

    except Exception as config_err:
        log(f"Error configuring API request for {model_name}: {config_err}", "ERROR", camera_name, camera_uuid)
        return None, None, calculate_cost(count_tokens(prompt_text, model_name), "", model_name)

    try:
        log(f"Sending request to {model_name.upper()} API...", "INFO", camera_name, camera_uuid)
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()

        response_data = response.json()
        response_content = ""

        if model_name == "openai":
            if "choices" in response_data and len(response_data["choices"]) > 0:
                message = response_data["choices"][0].get("message", {})
                response_content = message.get("content", "")
            else:
                log(f"Unexpected OpenAI response format: {response_data}", "WARNING", camera_name, camera_uuid)
        elif model_name == "gemini":
            if "promptFeedback" in response_data and "blockReason" in response_data["promptFeedback"]:
                 block_reason = response_data["promptFeedback"]["blockReason"]
                 log(f"Gemini request blocked due to: {block_reason}", "WARNING", camera_name, camera_uuid)
                 response_content = f"Blocked: {block_reason}"
            elif "candidates" in response_data and len(response_data["candidates"]) > 0:
                content = response_data["candidates"][0].get("content", {})
                if "parts" in content and len(content["parts"]) > 0:
                    response_content = content["parts"][0].get("text", "")
                else:
                     log(f"Unexpected Gemini response format (no parts): {response_data}", "WARNING", camera_name, camera_uuid)
            else:
                log(f"Unexpected Gemini response format: {response_data}", "WARNING", camera_name, camera_uuid)
        elif model_name == "claude":
             if response_data.get("type") == "error":
                 error_details = response_data.get("error", {})
                 log(f"Claude API error: {error_details.get('type')} - {error_details.get('message')}", "ERROR", camera_name, camera_uuid)
             elif "content" in response_data and len(response_data["content"]) > 0:
                 if response_data["content"][0].get("type") == "text":
                     response_content = response_data["content"][0].get("text", "")
                 else:
                     log(f"Unexpected Claude response content type: {response_data['content'][0].get('type')}", "WARNING", camera_name, camera_uuid)
             else:
                 log(f"Unexpected Claude response format: {response_data}", "WARNING", camera_name, camera_uuid)

        if not response_content:
             log(f"Could not extract content from {model_name} response.", "WARNING", camera_name, camera_uuid)
             cost_info = calculate_cost(count_tokens(prompt_text, model_name), "", model_name)
             return None, f"Failed to get response content from {model_name}", cost_info

        prompt_token_count = count_tokens(prompt_text, model_name)
        cost_info = calculate_cost(prompt_token_count, response_content, model_name)

        try:
            rating_match = re.search(r'\b[1-5]\b', response_content)
            if rating_match:
                rating = int(rating_match.group(0))

                cleaned_response = ' '.join(response_content.split())

                explanation_match = re.search(r'\b[1-5]\b.*?[-:](.+)', cleaned_response)
                if explanation_match:
                    explanation = explanation_match.group(1).strip()
                else:
                    parts = cleaned_response.split(str(rating), 1)
                    explanation = parts[1].strip() if len(parts) > 1 else "No explanation provided"

                log(f"({model_name.upper()}) Blur rating: {rating} /4 (1=blurry, 4=sharp) - {explanation}", "INFO", camera_name, camera_uuid)
                return rating, explanation, cost_info
            else:
                log(f"({model_name.upper()}) Could not extract numeric rating from response: {response_content}", "WARNING", camera_name, camera_uuid)
                return None, response_content, cost_info
        except Exception as parse_e:
            log(f"({model_name.upper()}) Failed to parse blur rating: {str(parse_e)}. Raw response: {response_content}", "ERROR", camera_name, camera_uuid)
            return None, response_content, cost_info

    except requests.exceptions.RequestException as req_e:
        log(f"Error calling {model_name.upper()} API: {str(req_e)}", "ERROR", camera_name, camera_uuid)
        cost_info = calculate_cost(count_tokens(prompt_text, model_name), "", model_name)
        return None, None, cost_info
    except Exception as e:
        log(f"Unexpected error during {model_name.upper()} analysis: {str(e)}", "ERROR", camera_name, camera_uuid)
        cost_info = calculate_cost(count_tokens(prompt_text, model_name), "", model_name)
        return None, None, cost_info

def save_image(image_data, camera_name, camera_uuid, is_blurry=False):
    """Save image to disk for reference"""
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    status = "_[BLURRY]_" if is_blurry else "_[CLEAR]_"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{IMAGE_DIR}/{camera_name}_{camera_uuid}_{status}_{timestamp}.jpg"
    
    try:
        with open(filename, "wb") as f:
            f.write(image_data)
        return filename
    except Exception as e:
        log(f"Error saving image: {str(e)}", "ERROR", camera_name, camera_uuid)
        return None

# Write the attention report to a file
def write_attention_report(attention_list):
    """Writes cameras requiring human attention to a report file."""
    if not attention_list:
        log("No cameras require human attention.")
        return

    report_filename = f"human_attention_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_filename, "w") as f:
            f.write("================= CAMERAS REQUIRING HUMAN ATTENTION =================\n\n")
            f.write(f"Report generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total cameras needing attention: {len(attention_list)}\n")
            f.write("===================================================================\n\n")

            for i, camera_info in enumerate(attention_list, 1):
                camera = camera_info.get("camera", {})
                camera_name = camera.get("name", "Unnamed")
                camera_uuid = camera.get("uuid", "N/A")
                location_id = camera_info.get("location", "N/A")
                reason = camera_info.get("reason", "N/A")
                blur_rating = camera_info.get("blur_rating", "N/A")
                explanation = camera_info.get("explanation", "N/A")
                image_path = camera_info.get("image_path", "N/A") # Get image path if available

                f.write(f"{i}. Camera: {camera_name} (UUID: {camera_uuid})\n")
                f.write(f"   Location UUID: {location_id}\n")
                f.write(f"   Reason: {reason}\n")
                f.write(f"   Last Blur Rating: {blur_rating} / 4\n")
                f.write(f"   Last Explanation: {explanation}\n")
                if image_path and image_path != "N/A": # Include image path if it exists
                    f.write(f"   Related Image: {os.path.abspath(image_path)}\n")
                f.write("-" * 60 + "\n")

        log(f"Human attention report saved to: {report_filename}")

    except IOError as e:
        log(f"Error writing attention report to file {report_filename}: {e}", "ERROR")
    except Exception as e:
        log(f"Unexpected error writing attention report: {e}", "ERROR")

def process_cameras(model_name, location_uuids=None):
    """Main function to process cameras and check for blurriness"""
    start_time = datetime.now()
    log(f"Starting camera processing at {start_time.strftime('%Y-%m-%d %H:%M:%S')} using model: {model_name.upper()}")
    
    # Create image directory if it doesn't exist
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    # Initialize cost tracking
    total_cost = 0
    total_images = 0
    total_blurry_detected = 0
    
    # Get all cameras once at the beginning
    log("Retrieving camera list...")
    all_cameras = get_all_cameras()
    if not all_cameras:
        log("No cameras found or error retrieving camera list", "ERROR")
        return
    
    log(f"Retrieved {len(all_cameras)} cameras")
    
    # Organize cameras by location - more efficient approach
    locations = {}
    for camera in all_cameras:
        location_id = camera.get("locationUuid", "unknown")
        if location_id not in locations:
            locations[location_id] = {
                "online": [],
                "offline": []
            }
        
        # Ignore offline devices
        if camera.get("connectionStatus") == "GREEN":
            locations[location_id]["online"].append(camera)
        else:
            locations[location_id]["offline"].append(camera)
    
    # Determine which locations to process
    if location_uuids:
        # Filter to only include locations that exist in our data
        target_locations = [loc for loc in location_uuids if loc in locations]
        if len(target_locations) < len(location_uuids):
            missing = set(location_uuids) - set(target_locations)
            log(f"Warning: {len(missing)} requested locations were not found: {', '.join(missing)}", "WARNING")
    else:
        target_locations = list(locations.keys())
    
    
    online_cameras = sum(len(locations[loc]["online"]) for loc in target_locations)
    offline_cameras = sum(len(locations[loc]["offline"]) for loc in target_locations)
    
    log(f"Processing {online_cameras} online cameras across {len(target_locations)} locations")
    log(f"Skipping {offline_cameras} offline cameras")
    
    # Initialize summary statistics for reporting
    cameras_processed = 0
    cameras_refocused = 0
    cameras_requiring_attention = 0
    human_attention_cameras = []
    
    # Process each target location
    for location_id in target_locations:
        target_cameras = locations[location_id]["online"]
        if not target_cameras:
            log(f"No online cameras found in location {location_id}, skipping")
            continue
            
        log(f"Processing {len(target_cameras)} online cameras in location {location_id}")
        
        # Process in smaller batches to improve performance
        batch_size = 10
        for i in range(0, len(target_cameras), batch_size):
            batch = target_cameras[i:i+batch_size]
            log(f"Processing batch of {len(batch)} cameras ({i+1}-{min(i+len(batch), len(target_cameras))} of {len(target_cameras)})")
            log("==================================================================")
            
            frame_uris = []
            camera_uri_map = {}
            
            # Get frame URIs for this batch
            for camera in batch:
                camera_uuid = camera.get("uuid")
                camera_name = camera.get("name", "Unnamed")
                
                log(f"Getting frame URI", "INFO", camera_name, camera_uuid)
                
                # Convert current time to unix ms
                current_time_ms = int(time.time() * 1000)
                
                frame_uri = get_frame_uri(camera_uuid, current_time_ms)
                if not frame_uri:
                    log(f"Could not get frame URI", "ERROR", camera_name, camera_uuid)
                    continue
                
                frame_uris.append(frame_uri)
                camera_uri_map[frame_uri] = camera
                
            log("==================================================================")
            # Skip if no valid URIs in this batch
            if not frame_uris:
                log("No valid frame URIs found for this batch, skipping")
                continue
                
            log(f"Downloading {len(frame_uris)} camera images...")
            downloaded_images = download_images_with_shared_token(frame_uris)
            
            # Track blurry cameras for this batch
            batch_blurry_cameras = []
            
            # Process downloaded images
            for frame_uri, image_data in downloaded_images.items():
                camera = camera_uri_map[frame_uri]
                camera_uuid = camera.get("uuid")
                camera_name = camera.get("name", "Unnamed")
                
                cameras_processed += 1
                total_images += 1
                
                # Analyze image for blurriness using the specified model
                blur_rating, explanation, cost_info = analyze_image_blurriness(image_data, model_name, camera_name, camera_uuid)
                total_cost += cost_info["total_cost"]
                
                if blur_rating is None:
                    log(f"Could not determine blur rating", "ERROR", camera_name, camera_uuid)
                    continue
                
                # Save the image with appropriate naming
                is_blurry = blur_rating <= BLURRINESS_THRESHOLD
                image_path = save_image(image_data, camera_name, camera_uuid, is_blurry)
                
                # If camera is blurry, add to list for refocusing
                if is_blurry:
                    total_blurry_detected += 1
                    log(f"Camera is blurry (rating: {blur_rating} /4) - {explanation}", "INFO", camera_name, camera_uuid)
                    batch_blurry_cameras.append({
                        "camera": camera,
                        "blur_rating": blur_rating,
                        "explanation": explanation,
                        "image_path": image_path
                    })
                    log("*************************DETECTED BLUR***************************")
                    log("==================================================================\n")
                else:
                    log(f"Camera is clear (rating: {blur_rating} /4). No action needed.", "INFO", camera_name, camera_uuid)
                    log("==================================================================\n")
                    
            
            if not batch_blurry_cameras:
                log("No blurry cameras found in this batch.")
                continue
                
            # Process blurry cameras for this batch
            cameras_refocused += len(batch_blurry_cameras)
            log(f"Triggering autofocus for {len(batch_blurry_cameras)} blurry cameras")
            
            # Trigger refocus and check results for blurry cameras
            for camera_info in batch_blurry_cameras:
                camera = camera_info["camera"]
                camera_uuid = camera.get("uuid")
                camera_name = camera.get("name", "Unnamed")
                
                success = trigger_camera_refocus(camera_uuid, camera_name)
                if not success:
                    log(f"Failed to trigger autofocus", "ERROR", camera_name, camera_uuid)
                    human_attention_cameras.append({
                        "camera": camera,
                        "location": location_id,
                        "reason": "Failed to trigger autofocus",
                        "blur_rating": camera_info["blur_rating"],
                        "explanation": camera_info["explanation"],
                        "image_path": camera_info.get("image_path") # Pass image path
                    })
                    cameras_requiring_attention += 1
                    continue
            
            # Wait for cameras to refocus (only if we successfully triggered any)
            if batch_blurry_cameras:
                log(f"Waiting {REFOCUS_WAIT_TIME} seconds for cameras to refocus...")
                time.sleep(REFOCUS_WAIT_TIME)
                
                # Check cameras after refocus
                frame_uris_after_refocus = []
                camera_uri_map_after_refocus = {}
                
                for camera_info in batch_blurry_cameras:
                    camera = camera_info["camera"]
                    camera_uuid = camera.get("uuid")
                    camera_name = camera.get("name", "Unnamed")
                    
                    log(f"Getting frame URI for re-checking", "INFO", camera_name, camera_uuid)
                    current_time_ms = int(time.time() * 1000)
                    
                    frame_uri = get_frame_uri(camera_uuid, current_time_ms)
                    if not frame_uri:
                        log(f"Could not get frame URI after refocus", "ERROR", camera_name, camera_uuid)
                        human_attention_cameras.append({
                            "camera": camera,
                            "location": location_id,
                            "reason": "Could not get frame URI after refocus",
                            "blur_rating": camera_info["blur_rating"],
                            "explanation": camera_info["explanation"],
                            "image_path": camera_info.get("image_path") # Pass image path
                        })
                        cameras_requiring_attention += 1
                        continue
                    
                    frame_uris_after_refocus.append(frame_uri)
                    camera_uri_map_after_refocus[frame_uri] = {
                        "camera": camera,
                        "previous_blur_rating": camera_info["blur_rating"],
                        "previous_explanation": camera_info["explanation"]
                    }
                
                if frame_uris_after_refocus:
                    log(f"Downloading {len(frame_uris_after_refocus)} camera images after refocusing...")
                    downloaded_images_after_refocus = download_images_with_shared_token(frame_uris_after_refocus)
                    
                    # Process downloaded images after refocusing
                    for frame_uri, image_data in downloaded_images_after_refocus.items():
                        camera_info = camera_uri_map_after_refocus[frame_uri]
                        camera = camera_info["camera"]
                        previous_blur_rating = camera_info["previous_blur_rating"]
                        previous_explanation = camera_info["previous_explanation"]
                        camera_uuid = camera.get("uuid")
                        camera_name = camera.get("name", "Unnamed")
                        
                        total_images += 1
                        
                        # Analyze image for blurriness using the specified model
                        blur_rating, explanation, cost_info = analyze_image_blurriness(image_data, model_name, camera_name, camera_uuid)
                        total_cost += cost_info["total_cost"]
                        
                        if blur_rating is None:
                            log(f"Could not determine blur rating after refocus", "ERROR", camera_name, camera_uuid)
                            human_attention_cameras.append({
                                "camera": camera,
                                "location": location_id,
                                "reason": "Could not determine blur rating after refocus",
                                "blur_rating": previous_blur_rating,
                                "explanation": previous_explanation,
                                "image_path": camera_info.get("image_path") # Pass image path (might be None if first save failed)
                            })
                            cameras_requiring_attention += 1
                            continue
                        
                        # Save the image with appropriate naming
                        is_blurry = blur_rating <= BLURRINESS_THRESHOLD
                        image_path = save_image(image_data, camera_name, camera_uuid, is_blurry)
                        
                        # If camera is still blurry, add to human attention list
                        if is_blurry:
                            log(f"Camera is still blurry after refocus (rating: {blur_rating} /4) - {explanation}", "INFO", camera_name, camera_uuid)
                            human_attention_cameras.append({
                                "camera": camera,
                                "location": location_id,
                                "reason": "Still blurry after refocus",
                                "blur_rating": blur_rating,
                                "explanation": explanation,
                                "image_path": image_path # Use the path of the *new* blurry image
                            })
                            cameras_requiring_attention += 1
                        else:
                            log(f"Camera is now clear after refocus (rating: {blur_rating} /4) - {explanation}", "INFO", camera_name, camera_uuid)

    # Generate report
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    log("\n======================== SUMMARY REPORT ========================")
    log(f"Process completed in {duration:.2f} seconds")
    log(f"Total locations processed: {len(target_locations)}")
    log(f"Total cameras processed: {cameras_processed}")
    log(f"Total blurry cameras detected: {total_blurry_detected}")
    log(f"Total cameras refocused: {cameras_refocused}")
    log(f"Total cameras still requiring attention: {cameras_requiring_attention}")
    log(f"Total images analyzed: {total_images}")
    log(f"Total ~ESTIMATED~ API cost: ${total_cost:.6f}")
    
    # Better to write the human attention report to a file instead of logging to console
    if human_attention_cameras:
        log(f"\n{len(human_attention_cameras)} cameras require human attention. Writing details to report file...")
        write_attention_report(human_attention_cameras)
    else:
        log("\nAll cameras checked are focused or were successfully refocused. No human attention required.")
    
    log("==================================================================")

def main():
    parser = argparse.ArgumentParser(description="Rhombus Auto-Focus Script")
    parser.add_argument('-clean', action='store_true', help='Clean up downloaded images when done')
    parser.add_argument('-location', action='append', help='Target location UUID(s) to process. Can be specified multiple times. If not specified, all locations will be processed.')
    parser.add_argument('-all', action='store_true', help='Process all locations (default behavior if no location is specified)')
    parser.add_argument('-model', type=str, default='openai', choices=['openai', 'gemini', 'claude'],
                        help='Specify the AI model to use for blurriness analysis (openai, gemini, claude). Default: openai')
    args = parser.parse_args()
    
    # Validate API keys based on selected model
    if args.model == "openai" and OPENAI_API_KEY == "YOUR_OPENAI_API_KEY":
        log("OpenAI API Key is incorrect or is a placeholder. Please replace it.", "ERROR")
        return
    elif args.model == "gemini" and GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        log("Gemini API Key is incorrect or is a placeholder. Please replace it.", "ERROR")
        return
    elif args.model == "claude" and ANTHROPIC_API_KEY == "YOUR_ANTHROPIC_API_KEY":
        log("Anthropic API Key is incorrect or is a placeholder. Please replace it.", "ERROR")
        return

    try:
        # Determine which locations to process
        location_uuids = None  # None means "all locations"
        if args.location:
            location_uuids = args.location
            log(f"Processing specific locations: {', '.join(location_uuids)}")
        else:
            log("Processing all locations (no specific locations provided)")
        
        process_cameras(args.model, location_uuids)
        
        # Clean up images if requested
        if args.clean and os.path.exists(IMAGE_DIR):
            log(f"Cleaning up images in {IMAGE_DIR}")
            shutil.rmtree(IMAGE_DIR)
            log("Image cleanup complete")
            
    except KeyboardInterrupt:
        log("Process interrupted by user", "WARNING")
    except Exception as e:
        log(f"Unexpected error: {str(e)}", "ERROR")
        import traceback
        log(traceback.format_exc(), "ERROR")

if __name__ == "__main__":
    main()