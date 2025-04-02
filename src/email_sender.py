import os
import boto3
import logging
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger("daily_feed")

def format_email(feed_entries, ainews_content, summary, current_date):
    """
    Format the email content with feed entries, AI News content, and summary.
    
    Args:
        feed_entries (list): List of feed entry dictionaries
        ainews_content (dict): AI News content dictionary or None
        summary (str): The generated summary text
        current_date (datetime): The current date
        
    Returns:
        tuple: (HTML body, plain text body)
    """
    date_str = current_date.strftime("%A, %B %d, %Y")
    
    # Start building HTML and plain text content
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 800px; margin: 0 auto; padding: 20px; }}
            h1, h2, h3 {{ color: #2c3e50; }}
            .summary {{ background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin-bottom: 20px; }}
            .feed-entry {{ margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }}
            .feed-entry h3 {{ margin-bottom: 5px; }}
            .feed-entry .source {{ color: #7f8c8d; font-size: 0.9em; margin-bottom: 8px; }}
            .snippet {{ color: #555; }}
            .no-content {{ color: #e74c3c; font-style: italic; }}
        </style>
    </head>
    <body>
        <h1>Daily Feed Summary - {date_str}</h1>
        
        <div class="summary">
            <h2>Summary</h2>
            <p>{summary}</p>
        </div>
    """
    
    text_content = f"""DAILY FEED SUMMARY - {date_str}

SUMMARY
{summary}

"""
    
    # Add Feed Entries section
    html_content += "<h2>Feed Updates</h2>"
    text_content += "\nFEED UPDATES\n"
    
    if feed_entries:
        for entry in feed_entries:
            html_content += f"""
            <div class="feed-entry">
                <h3><a href="{entry['link']}">{entry['title']}</a></h3>
                <p class="source">Source: {entry['source']}</p>
                <div class="snippet">{entry['snippet']}</div>
            </div>
            """
            
            text_content += f"""
* {entry['title']}
  Source: {entry['source']}
  Link: {entry['link']}
  
  {entry['snippet']}
  
"""
    else:
        html_content += '<p class="no-content">No new feed updates for today.</p>'
        text_content += "No new feed updates for today.\n"
    
    # Add AI News section
    html_content += "<h2>AI News Update</h2>"
    text_content += "\nAI NEWS UPDATE\n"
    
    if ainews_content:
        logger.debug(f"AI News content keys: {ainews_content.keys()}")
        logger.debug(f"AI News content snippet: {ainews_content.get('snippet', 'No snippet')}")
        logger.debug(f"AI News content full: {ainews_content.get('content', 'No content')[:100]}...")  # First 100 chars
        html_content += f"""
        <div class="feed-entry">
            <h3><a href="{ainews_content['link']}">{ainews_content['title']}</a></h3>
            <p class="source">Source: {ainews_content['source']}</p>
            <div class="content">
                {ainews_content['content']}
            </div>
        </div>
        """
        
        text_content += f"""
* {ainews_content['title']}
  Source: {ainews_content['source']}
  Link: {ainews_content['link']}
  
  {ainews_content['content']}
"""
    else:
        html_content += f'<p class="no-content">No AI News article available for {date_str}.</p>'
        text_content += f"No AI News article available for {date_str}.\n"
    
    # Close HTML
    html_content += """
    </body>
    </html>
    """
    
    return html_content, text_content

def send_email(subject, body_html, body_text):
    """
    Send an email using AWS SES or the local SMTP method for testing.
    
    Args:
        subject (str): Email subject
        body_html (str): HTML version of the email body
        body_text (str): Plain text version of the email body
        
    Returns:
        bool: True if email sent successfully, False otherwise
    """
    recipient = os.environ.get('RECIPIENT_EMAIL')
    sender = os.environ.get('SENDER_EMAIL', recipient)  # Default to recipient if sender not specified
    
    if not recipient:
        logger.error("RECIPIENT_EMAIL environment variable not set")
        return False
    
    # For testing, you can force AWS SES mode with an environment variable
    force_ses = os.environ.get('FORCE_SES', 'false').lower() == 'true'
    is_aws = os.environ.get('AWS_EXECUTION_ENV') is not None
    
    # Add debug logging
    logger.info(f"Email sending configuration:")
    logger.info(f"- Recipient: {recipient}")
    logger.info(f"- Sender: {sender}")
    logger.info(f"- FORCE_SES: {force_ses}")
    logger.info(f"- Is AWS environment: {is_aws}")
    logger.info(f"- Will use SES: {is_aws or force_ses}")
    
    if is_aws or force_ses:
        return _send_email_aws_ses(subject, body_html, body_text, sender, recipient)
    else:
        return _send_email_local(subject, body_html, body_text, sender, recipient)

def _send_email_aws_ses(subject, body_html, body_text, sender, recipient):
    """Send email using AWS SES"""
    try:
        # Create SES client with explicit region
        region = os.environ.get('AWS_REGION', 'us-east-1')
        logger.info(f"Creating SES client in region {region}...")
        ses = boto3.client('ses', region_name=region)
        
        logger.info(f"Sending email via SES from {sender} to {recipient}")
        
        # Create message
        response = ses.send_email(
            Source=sender,
            Destination={
                'ToAddresses': [recipient]
            },
            Message={
                'Subject': {'Data': subject},
                'Body': {
                    'Text': {'Data': body_text},
                    'Html': {'Data': body_html}
                }
            }
        )
        
        logger.info(f"Email sent via AWS SES: {response['MessageId']}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email via AWS SES: {str(e)}")
        # Print the full traceback for debugging
        import traceback
        logger.error(traceback.format_exc())
        return False

def _send_email_local(subject, body_html, body_text, sender, recipient):
    """
    For local testing/development, write email to a file instead of sending.
    In a production environment, you'd integrate with your email system.
    """
    try:
        # Create a directory for email output
        os.makedirs('email_output', exist_ok=True)
        
        # Create a timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Write HTML email to file
        html_file = f"email_output/email_{timestamp}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(body_html)
        
        # Write text email to file
        text_file = f"email_output/email_{timestamp}.txt"
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write(f"Subject: {subject}\nFrom: {sender}\nTo: {recipient}\n\n{body_text}")
        
        logger.info(f"Email saved locally to {html_file} and {text_file}")
        print(f"Email saved locally to {html_file} and {text_file}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to save email locally: {str(e)}")
        return False