"""Multimodal ingestion service for program analysis."""
import base64
import io
import json
import logging
from typing import Any
from PIL import Image

logger = logging.getLogger(__name__)


class MultimodalIngestion:
    """Service for analyzing programs using multiple modalities."""

    def __init__(self, openai_service=None):
        self.openai_service = openai_service

    async def analyze_with_vision(
        self,
        image_bytes: bytes,
        prompt: str | None = None
    ) -> dict[str, Any]:
        """Analyze an image using vision model."""
        if len(image_bytes) > 20 * 1024 * 1024:
            return {"error": "Image too large (max 20MB)"}

        if not self.openai_service:
            return {"error": "OpenAI service not configured"}

        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        default_prompt = """You are analyzing a document from a bug bounty program. Extract ALL of the following:
1. Domain names and URLs
2. IP addresses
3. Technology names (frameworks, libraries, services)
4. Authentication methods (OAuth, SAML, JWT, 2FA, etc.)
5. API endpoints or patterns
6. File names or paths
7. Any credentials, tokens, or keys visible
8. Architecture components or services
9. Any attack vectors or vulnerability mentions
10. Testing instructions or guidelines

Return a structured JSON with all findings."""

        try:
            response = await self.openai_service.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt or default_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw_text": content}

        except Exception as e:
            logger.error(f"Vision analysis error: {e}")
            return {"error": str(e)}

    async def analyze_pdf_with_vision(
        self,
        pdf_bytes: bytes,
        page_limit: int = 10
    ) -> dict[str, Any]:
        """Extract images from PDF and analyze with vision."""
        try:
            import pdfplumber
            
            findings = {
                "text_content": [],
                "images_analyzed": 0,
                "images_findings": [],
                "combined_findings": {
                    "domains": [],
                    "ips": [],
                    "technologies": [],
                    "auth_methods": [],
                    "endpoints": [],
                    "credentials": [],
                    "attack_vectors": [],
                    "architecture": []
                }
            }

            with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
                page_count = min(len(pdf.pages), page_limit)
                
                for page_num, page in enumerate(pdf.pages[:page_count]):
                    page_text = page.extract_text()
                    if page_text:
                        findings["text_content"].append({
                            "page": page_num + 1,
                            "text": page_text
                        })

                    images = page.images
                    for img_idx, img_info in enumerate(images):
                        try:
                            if img_info.get("width", 0) > 100 and img_info.get("height", 0) > 100:
                                clip = img_info.get("x0", 0), img_info.get("top", 0), img_info.get("x1", 0), img_info.get("bottom", 0)
                                cropped = page.crop(clip)
                                img_data = cropped.to_image()
                                
                                img_bytes = io.BytesIO()
                                img_data.save(img_bytes, format="PNG")
                                img_bytes = img_bytes.getvalue()

                                img_analysis = await self.analyze_with_vision(
                                    img_bytes,
                                    prompt="""Analyze this image from a bug bounty program document. Extract:
1. Architecture diagrams or flowcharts
2. Network topology or infrastructure details
3. Any visible domain names or IPs
4. Technology logos or service names
5. Authentication flow diagrams
6. Any credentials or tokens visible
7. Attack path diagrams
8. Configuration examples

Return JSON with all findings."""
                                )

                                if "error" not in img_analysis:
                                    findings["images_analyzed"] += 1
                                    findings["images_findings"].append({
                                        "page": page_num + 1,
                                        "image_index": img_idx,
                                        "analysis": img_analysis
                                    })
                                    self._merge_findings(findings["combined_findings"], img_analysis)

                        except Exception as e:
                            logger.warning(f"Failed to analyze image on page {page_num + 1}: {e}")

            return findings

        except Exception as e:
            logger.error(f"PDF vision analysis error: {e}")
            return {"error": str(e)}

    async def analyze_video_frames(
        self,
        video_path: str,
        frame_interval_seconds: int = 5
    ) -> dict[str, Any]:
        """Extract frames from video and analyze with vision."""
        try:
            import cv2

            findings = {
                "frames_analyzed": 0,
                "frame_findings": [],
                "combined_findings": {
                    "domains": [],
                    "ips": [],
                    "technologies": [],
                    "auth_methods": [],
                    "credentials": [],
                    "endpoints": [],
                    "attack_vectors": []
                }
            }

            cap = cv2.VideoCapture(video_path)
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_interval = int(fps * frame_interval_seconds)
            frame_count = 0
            analyzed_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                if frame_count % frame_interval == 0:
                    _, buffer = cv2.imencode(".jpg", frame)
                    frame_bytes = buffer.tobytes()

                    analysis = await self.analyze_with_vision(
                        frame_bytes,
                        prompt="""Analyze this video frame from a security testing demonstration. Extract:
1. Any visible URLs, domains, or IP addresses
2. Authentication credentials shown
3. Technology or tool interfaces visible
4. API endpoints or request/response data
5. Configuration values or tokens
6. Any security testing techniques demonstrated

Return JSON with all findings."""
                    )

                    if "error" not in analysis:
                        analyzed_count += 1
                        findings["frame_findings"].append({
                            "frame_number": frame_count,
                            "timestamp_seconds": frame_count / fps if fps > 0 else 0,
                            "analysis": analysis
                        })
                        self._merge_findings(findings["combined_findings"], analysis)

                frame_count += 1

                if analyzed_count >= 30:
                    break

            cap.release()
            findings["frames_analyzed"] = analyzed_count
            return findings

        except Exception as e:
            logger.error(f"Video analysis error: {e}")
            return {"error": str(e)}

    async def analyze_code_snippet(
        self,
        code: str,
        language: str | None = None
    ) -> dict[str, Any]:
        """Analyze code for security implications and attack surface."""
        if not self.openai_service:
            return {"error": "OpenAI service not configured"}

        prompt = f"""Analyze this code for a bug bounty program assessment. Identify:
1. API endpoints or routes
2. Authentication/authorization mechanisms
3. Input validation patterns
4. Known vulnerable patterns (SQL injection, XSS, etc.)
5. Configuration values that might be credentials
6. Third-party services or integrations
7. Potential attack vectors

Language: {language or "auto-detected"}

Return a structured JSON analysis."""

        try:
            response = await self.openai_service.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a security researcher analyzing code for vulnerabilities."},
                    {"role": "user", "content": prompt + "\n\n```" + code + "```"}
                ],
                max_tokens=2048,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"Code analysis error: {e}")
            return {"error": str(e)}

    async def generate_custom_script(
        self,
        target_description: str,
        attack_type: str,
        constraints: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Generate a custom exploitation script based on requirements."""
        if not self.openai_service:
            return {"error": "OpenAI service not configured"}

        constraint_str = ""
        if constraints:
            constraint_str = "\n".join([f"- {k}: {v}" for k, v in constraints.items()])

        prompt = f"""Generate a Python script for security testing.

Target: {target_description}
Attack Type: {attack_type}

Constraints:
{constraint_str or "No specific constraints"}

Requirements:
1. Use asyncio for concurrent requests
2. Include proper error handling
3. Add detailed logging
4. Include response analysis
5. Follow security testing best practices
6. Include comments explaining each step

Return JSON with:
- "script": the complete Python code
- "description": what the script does
- "requirements": pip packages needed
- "usage": how to run the script
- "safety_notes": precautions to take"""

        try:
            response = await self.openai_service.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {
                        "role": "system",
                        "content": """You are an expert security researcher who writes Python scripts for penetration testing. 
Always include proper error handling and logging. Never include malicious code that could cause harm."""
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=8192,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except Exception as e:
            logger.error(f"Script generation error: {e}")
            return {"error": str(e)}

    def _merge_findings(self, combined: dict, new: dict) -> None:
        """Merge findings from different analyses."""
        for key in combined:
            if key in new:
                value = new[key]
                if isinstance(value, list):
                    combined[key] = list(set(combined[key] + value))
                elif isinstance(value, str) and value not in combined[key]:
                    combined[key].append(value)


multimodal_ingestion = MultimodalIngestion()
