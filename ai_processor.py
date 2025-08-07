from anthropic import Anthropic
import cv2
import numpy as np
import base64
import json
from typing import Dict, Any, Optional
import os
from dotenv import load_dotenv

load_dotenv()

class AnthropicAIProcessor:
    def __init__(self):
        self.client = Anthropic(
            api_key=os.getenv('ANTHROPIC_API_KEY')
        )
    
    def encode_image(self, image: np.ndarray) -> str:
        """Convert OpenCV image to base64 string"""
        _, buffer = cv2.imencode('.jpg', image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        return image_base64
    
    def analyze_frame(self, frame: np.ndarray, analysis_type: str = "general") -> Dict[str, Any]:
        """Analyze frame using Anthropic Claude Vision"""
        try:
            image_base64 = self.encode_image(frame)
            
            # Define different prompts based on analysis type
            prompts = {
                "object_detection": """
                Analyze this image and identify all objects visible. For each object, provide:
                1. Object type/class
                2. Confidence level (0-1)
                3. Approximate location description
                4. Size estimation (small/medium/large)
                
                Return the response in JSON format with an 'objects' array.
                """,
                
                "defect_analysis": """
                Examine this image for any defects, anomalies, or quality issues. Look for:
                1. Scratches, dents, or surface damage
                2. Color inconsistencies
                3. Structural problems
                4. Missing components
                
                For each defect found, provide:
                - Type of defect
                - Severity level (minor/moderate/severe)
                - Location description
                - Confidence level
                
                Also provide an overall quality score (0-1). Return in JSON format.
                """,
                
                "asset_tracking": """
                Analyze this image to identify and track assets/equipment. Look for:
                1. Industrial equipment
                2. Vehicles
                3. People/personnel
                4. Tools or machinery
                5. Safety equipment
                
                For each asset, provide:
                - Asset type
                - Status (operational/maintenance/inactive)
                - Location in frame
                - Any safety concerns
                
                Return in JSON format with an 'assets' array.
                """,
                
                "general": """
                Perform a comprehensive analysis of this image. Identify:
                1. All visible objects and their types
                2. Any potential safety hazards
                3. Overall scene description
                4. Activity level (high/medium/low)
                5. Any anomalies or points of interest
                
                Return the analysis in JSON format.
                """
            }
            
            prompt = prompts.get(analysis_type, prompts["general"])
            
            message = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # Parse the response
            response_text = message.content[0].text
            
            # Try to extract JSON from the response
            try:
                # Find JSON in the response
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    return json.loads(json_str)
                else:
                    # Fallback: return structured response
                    return {
                        "analysis": response_text,
                        "confidence": 0.8,
                        "timestamp": "N/A"
                    }
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw text analysis
                return {
                    "analysis": response_text,
                    "confidence": 0.8,
                    "raw_response": True
                }
                
        except Exception as e:
            print(f"Error in Anthropic analysis: {e}")
            return {
                "error": str(e),
                "analysis": "Analysis failed",
                "confidence": 0.0
            }
    
    def batch_analyze_images(self, images: list, analysis_type: str = "general") -> list:
        """Analyze multiple images in batch"""
        results = []
        for i, image in enumerate(images):
            result = self.analyze_frame(image, analysis_type)
            result["image_index"] = i
            results.append(result)
        return results
