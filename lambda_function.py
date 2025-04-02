import os
import json
import boto3
from datetime import datetime, timedelta, timezone
import traceback

# Import our modules
from src.feed_parser import get_feed_entries
from src.web_scraper import scrape_ainews
from src.summarizer import generate_summary
from src.email_sender import format_email, send_email
from src.utils import setup_logging

# Setup logger
logger = setup_logging()

def lambda_handler(event, context):
    """
    AWS Lambda handler function that fetches RSS feeds and web content,
    summarizes it, and emails the results.
    """
    try:
        logger.info("Starting Daily Feed Summary process")
        
        # Get today's date
        today = datetime.now(timezone.utc)
        logger.info(f"Processing feeds for date: {today.strftime('%Y-%m-%d')}")
        
        # Step 1: Fetch feed entries from sources.txt
        feed_entries = get_feed_entries(today)
        
        # Step 2: Scrape AI News content
        ainews_content = scrape_ainews(today)
        
        # If no content was found anywhere, send a notification email
        if not feed_entries and not ainews_content:
            logger.warning("No content found for today")
            send_email(
                subject=f"Daily Feed Summary - No Content ({today.strftime('%Y-%m-%d')})",
                body_html=f"<p>No new content was found for {today.strftime('%Y-%m-%d')}.</p>",
                body_text=f"No new content was found for {today.strftime('%Y-%m-%d')}."
            )
            return {
                'statusCode': 200,
                'body': json.dumps('Daily Feed Summary - No content found')
            }
        
        # Step 3: Generate summary of content
        all_content_text = ""
        
        # Include feed entries in the text to summarize
        for entry in feed_entries:
            all_content_text += f"Title: {entry['title']}\n{entry['snippet'][:15]}...\n\n"
            
        # Include AI News content if available
        if ainews_content:
            all_content_text += f"AI News: {ainews_content['title']}\n{ainews_content['snippet']}\n\n"
        
        # Generate summary using LLM
        summary = generate_summary(all_content_text)
        
        # Step 4: Format and send email
        email_html, email_text = format_email(feed_entries, ainews_content, summary, today)
        
        send_email(
            subject=f"Daily Feed Summary - {today.strftime('%Y-%m-%d')}",
            body_html=email_html,
            body_text=email_text
        )
        
        logger.info("Daily Feed Summary completed successfully")
        return {
            'statusCode': 200,
            'body': json.dumps('Daily Feed Summary process completed successfully')
        }
    
    except Exception as e:
        error_msg = f"Error in Daily Feed Summary: {str(e)}\n{traceback.format_exc()}"
        logger.error(error_msg)
        
        # Send error notification email
        try:
            send_email(
                subject=f"Daily Feed Summary - ERROR ({today.strftime('%Y-%m-%d')})",
                body_html=f"<p>An error occurred during the Daily Feed Summary process:</p><pre>{error_msg}</pre>",
                body_text=f"An error occurred during the Daily Feed Summary process:\n\n{error_msg}"
            )
        except Exception as email_error:
            logger.error(f"Failed to send error notification: {str(email_error)}")
        
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }

# For local testing
if __name__ == "__main__":
    # Use environment variables or .env file for local testing
    from dotenv import load_dotenv
    load_dotenv()
    
    # Call the handler with empty event
    result = lambda_handler({}, None)
    print(result)