import httpx
from typing import List
from fastapi import APIRouter, HTTPException, status
from app.core.config import settings
from app.schemas.flashcard import FlashcardRequest, FlashcardResponse, Flashcard
import json
import re

router = APIRouter(prefix="/flashcards")

# Constants
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1"
API_TIMEOUT = 30.0
MIN_NOTE_CONTENT_LENGTH = 10
MAX_NOTE_CONTENT_LENGTH = 5000
MAX_FLASHCARDS = 5
MAX_PREVIEW_LENGTH = 100


async def generate_flashcards_with_gemini(note_content: str) -> List[Flashcard]:
    """
    Generate flashcards using Google Gemini AI API via REST API.
    
    Args:
        note_content: The text content from which to generate flashcards
        
    Returns:
        List of Flashcard objects with question and answer pairs
        
    Raises:
        HTTPException: If API call fails or API key is missing
    """
    if not settings.gemini_api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Gemini API key not configured. Please set GEMINI_API_KEY in environment variables."
        )
    
    # Create the prompt for flashcard generation
    prompt = f"""Based on the following text, generate 3-5 educational flashcard questions and answers in Turkish.

IMPORTANT: You must respond ONLY with a valid JSON array. Do not include any markdown formatting, code blocks, or explanations.

Format your response as a JSON array like this example:
[{{"question": "Fotosentez nedir?", "answer": "Bitkilerin güneş ışığını kullanarak glikoz ürettiği süreç"}}, {{"question": "...", "answer": "..."}}]

Rules:
1. Create 3-5 flashcards
2. Questions should be clear, specific, and test understanding
3. Answers should be concise but complete (1-2 sentences)
4. Use Turkish language for both questions and answers
5. Focus on key concepts, definitions, processes, or important facts
6. Make questions diverse (what, how, why, when, where)
7. Response must be ONLY valid JSON - no extra text or markdown

Text to analyze:
{note_content}

Generate flashcards now (JSON only):"""

    # Use REST API endpoint
    api_url = f"{GEMINI_API_BASE_URL}/models/{settings.gemini_model}:generateContent"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }],
        "generationConfig": {
            "temperature": 0.7,
            "topK": 40,
            "topP": 0.95,
            "maxOutputTokens": 1024,
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=API_TIMEOUT) as client:
            response = await client.post(
                f"{api_url}?key={settings.gemini_api_key}",
                json=payload,
                headers=headers
            )
            
            # Handle specific API errors
            if response.status_code == 401:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid Google Gemini API key"
                )
            elif response.status_code == 429:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Gemini API rate limit exceeded. Please try again later."
                )
            elif response.status_code == 400:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get("message", response.text)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Gemini API error: {error_msg}"
                )
            elif response.status_code != 200:
                error_data = response.json() if response.content else {}
                error_msg = error_data.get("error", {}).get("message", response.text)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"Gemini API error: {error_msg}"
                )
            
            result = response.json()
            
            # Extract generated text from response
            if "candidates" not in result or not result["candidates"]:
                raise ValueError("No candidates in API response")
            
            candidate = result["candidates"][0]
            if "content" not in candidate or "parts" not in candidate["content"]:
                raise ValueError("No content in candidate response")
            
            response_text = candidate["content"]["parts"][0]["text"].strip()
            
            # Remove markdown code blocks if present
            response_text = re.sub(r'^```json\s*', '', response_text)
            response_text = re.sub(r'^```\s*', '', response_text)
            response_text = re.sub(r'\s*```$', '', response_text)
            response_text = response_text.strip()
            
            # Parse JSON response
            try:
                flashcards_data = json.loads(response_text)
            except json.JSONDecodeError:
                # Try to extract JSON array from text
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    flashcards_data = json.loads(json_match.group(0))
                else:
                    raise ValueError("Could not parse JSON from response")
            
            # Validate and convert to Flashcard objects
            if not isinstance(flashcards_data, list):
                raise ValueError("Response is not a JSON array")
            
            flashcards = []
            for item in flashcards_data[:MAX_FLASHCARDS]:
                if isinstance(item, dict) and "question" in item and "answer" in item:
                    flashcards.append(Flashcard(
                        question=item["question"].strip(),
                        answer=item["answer"].strip()
                    ))
            
            if not flashcards:
                raise ValueError("No valid flashcards found in response")
            
            return flashcards
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Gemini API request timed out. Please try again."
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to connect to Gemini API: {str(e)}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(e)}"
        )


@router.post(
    "/generate",
    response_model=FlashcardResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate flashcards from note content using AI",
    description="Uses Google Gemini AI to generate educational flashcards from note text"
)
async def generate_flashcards(body: FlashcardRequest) -> FlashcardResponse:
    """
    Generate flashcards from note content using Google Gemini AI.
    
    - **note_content**: The text content from which to generate flashcards
    
    Returns a list of question-answer pairs suitable for study and review.
    """
    try:
        # Validate input
        if not body.note_content or len(body.note_content.strip()) < MIN_NOTE_CONTENT_LENGTH:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Note content must be at least {MIN_NOTE_CONTENT_LENGTH} characters long"
            )
        
        # Truncate very long content to avoid API limits
        note_content = body.note_content
        if len(note_content) > MAX_NOTE_CONTENT_LENGTH:
            note_content = note_content[:MAX_NOTE_CONTENT_LENGTH] + "..."
        
        # Generate flashcards using Gemini AI
        flashcards = await generate_flashcards_with_gemini(note_content)
        
        # Create preview of input
        preview = body.note_content[:MAX_PREVIEW_LENGTH] + "..." if len(body.note_content) > MAX_PREVIEW_LENGTH else body.note_content
        
        return FlashcardResponse(
            flashcards=flashcards,
            note_content_preview=preview
        )
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        print(f"Error generating flashcards: {e}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate flashcards: {str(e)}"
        )
