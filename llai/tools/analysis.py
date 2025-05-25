from typing import Annotated, Dict, Any
from pydantic import Field
from legion import tool  # Removed LLM import

@tool
async def readability_analyzer(
    text: Annotated[str, Field(description="Text content to analyze for readability")],
    target_audience: Annotated[str, Field(description="Target audience (e.g., 'legal professionals', 'general public')")] = "general public",
    content_purpose: Annotated[str, Field(description="Purpose of the content (e.g., 'marketing', 'educational')")] = "marketing",
    llm: Annotated[Any, Field(description="LLM instance to use for analysis")] = None
) -> Dict[str, Any]:
    """
    Analyze text readability using AI-powered assessment rather than fixed formulas.
    
    This tool provides nuanced readability analysis by considering context, audience, 
    and purpose rather than just applying standard readability formulas. It extracts
    basic statistics and then uses an LLM to provide intelligent analysis.
    
    Returns a dictionary with readability assessment and recommendations.
    """
    import re
    # Clean the text
    clean_text = re.sub(r'\s+', ' ', text).strip()
    
    if len(clean_text) > 1000:
        clean_text = clean_text[:1000]
    
    # Basic counts
    words = clean_text.split()
    word_count = len(words)
    
    # Count sentences
    sentence_endings = re.findall(r'[.!?]+', clean_text)
    sentence_count = len(sentence_endings) if sentence_endings else 1
    
    # Average words per sentence
    avg_words_per_sentence = word_count / max(1, sentence_count)
    
    # Prepare statistics context
    stats_context = (
        f"Text statistics: {word_count} words, {sentence_count} sentences, "
        f"average of {avg_words_per_sentence:.1f} words per sentence."
    )
    
    # If no LLM is provided, return just the basic statistics
    if llm is None:
        return {
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": round(avg_words_per_sentence, 1),
            "note": "For full AI-powered analysis, an LLM instance must be provided."
        }
    
    # Create prompt for LLM analysis
    prompt = f"""
    Analyze the readability of the following text for a {target_audience} audience, 
    with the purpose of {content_purpose}. 
    
    {stats_context}
    
    Text to analyze:
    "{text[:100]}"
    
    Provide a detailed readability assessment including:
    1. Overall readability level
    2. Appropriateness for the target audience
    3. Strengths in terms of clarity and comprehension
    4. Areas that could be improved
    5. Specific recommendations for improving readability
    
    Format your response as a JSON object with the following keys:
    - readability_level: a string describing the overall readability
    - audience_appropriateness: a score from 1-10 and brief explanation
    - strengths: an array of readability strengths
    - improvement_areas: an array of areas that could be improved
    - recommendations: an array of specific recommendations
    - statistics: the basic text statistics
    """
    
    try:
        response = await llm.generate(prompt, response_format={"type": "json_object"})
        analysis = response.json()
        
        if "statistics" not in analysis:
            analysis["statistics"] = {
                "word_count": word_count,
                "sentence_count": sentence_count,
                "avg_words_per_sentence": round(avg_words_per_sentence, 1)
            }
        
        return analysis
    except Exception as e:
        return {
            "error": f"LLM analysis failed: {str(e)}",
            "word_count": word_count,
            "sentence_count": sentence_count,
            "avg_words_per_sentence": round(avg_words_per_sentence, 1)
        }
