import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
logger = logging.getLogger("daily_feed")

def generate_summary(text):
    """
    Generate a summary of the provided text using OpenAI API.
    
    Args:
        text (str): The text to summarize
        
    Returns:
        str: The summary text or an error message
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if OpenAI API key is available
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        logger.error("OPENAI_API_KEY environment variable not set")
        return "Summary not available (API key not set)"
    
    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=api_key)
        
        # Truncate text if too long
        max_input_length = 3000
        truncated_text = text[:max_input_length] if len(text) > max_input_length else text
        
        if len(text) > max_input_length:
            logger.warning(f"Text truncated from {len(text)} to {max_input_length} characters for summarization")
        
        # Call OpenAI API
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that summarizes news feed content. Create a concise 4-5 sentence summary that captures the key information from the feeds. Focus on new breakthroughs and new things that could have big impact rather than on some minor improvements. List also 5 biggest things happening based on impact they could have"},
                {"role": "user", "content": truncated_text}
            ],
            max_tokens=190,  # This sets the maximum number of tokens (words or characters) in the generated summary.
            temperature=0.0  # This controls the randomness of the generated text. A temperature of 0.0 means the model will always choose the most likely next word, resulting in a more deterministic and less creative output.
        )
        
        # Extract summary from response
        summary = response.choices[0].message.content.strip()
        logger.info(f"Generated summary ({len(summary)} chars)")
        
        return summary
        
    except Exception as e:
        error_msg = f"Summary generation failed: {str(e)}"
        logger.error(error_msg)
        return error_msg