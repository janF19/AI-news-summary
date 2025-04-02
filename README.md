# Daily Feed Summary Emailer

A Python application that fetches RSS/Atom feeds and web-scraped content, summarizes it with an LLM, and emails the results. This code can run locally for development and as an AWS Lambda function for production.

## Project Overview

This application automates the daily collection of news from:
- RSS/Atom feeds specified in `sources.txt`
- A scraped webpage (buttondown.com/ainews/archive/)

It then:
1. Processes the data into a structured format
2. Summarizes the content using OpenAI's GPT-3.5 Turbo
3. Sends an email with both the raw data and summary

## Setup

### Requirements

- Python 3.9 or later
- AWS account (for production deployment)
- OpenAI API key

### Local Development Setup

1. Clone the repository
2. Create a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
4. Create a `.env` file with your configuration:
   ```
   OPENAI_API_KEY=your_openai_api_key
   RECIPIENT_EMAIL=your_email@example.com
   SENDER_EMAIL=your_sender@example.com  # Optional, defaults to recipient
   ```
5. Create a `sources.txt` file with your RSS/Atom feeds:
   ```
   rss https://example.com/feed.xml
   atom https://another-example.com/atom.xml
   ```

### Running Locally

To run the application locally:

```
python lambda_function.py
```

This will:
- Fetch the feeds and web content
- Generate a summary
- Save the HTML and text versions of the email to the `email_output` directory

### AWS Deployment

To deploy to AWS Lambda:

1. Create a deployment package:
   ```
   pip install -r requirements.txt -t .
   zip -r deployment.zip lambda_function.py src/ sources.txt
   ```

2. Create an AWS Lambda function with Python 3.9 runtime

3. Upload the ZIP file to Lambda

4. Set environment variables in the Lambda configuration:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `RECIPIENT_EMAIL`: Email address to receive summaries
   - `SENDER_EMAIL`: (Optional) Email address to send from
   - `FORCE_SES`: Set to `TRUE` for Lambda deployment

5. Configure AWS SES for email delivery:
   - Verify your sender and recipient email addresses
   - If in sandbox mode, both sender and recipient must be verified

6. Create an EventBridge rule to trigger the Lambda function daily:
   - Schedule expression: `cron(0 8 * * ? *)` (8:00 AM UTC daily)
   - Target: Your Lambda function

7. Configure Lambda timeout to at least 30 seconds (1-2 minutes recommended)

## Project Structure

- `lambda_function.py`: Main Lambda handler
- `src/`: Source code modules
  - `feed_parser.py`: RSS/Atom feed processing
  - `web_scraper.py`: Web scraping functionality
  - `summarizer.py`: LLM summarization
  - `email_sender.py`: Email formatting and sending
  - `utils.py`: Helper functions
- `sources.txt`: List of RSS/Atom feed sources
- `requirements.txt`: Dependencies