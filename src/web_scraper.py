import requests
from bs4 import BeautifulSoup
import logging
import tempfile
import os

logger = logging.getLogger("daily_feed")

def scrape_ainews(current_date):
    """
    Scrape AI News website for the latest content matching the current date.
    
    Args:
        current_date (datetime): The date to find content for
        
    Returns:
        dict: Dictionary with AI News content or None if not found
    """
    archive_url = "https://buttondown.com/ainews/archive/"
    
    try:
        # Find article link for the current date
        article_url = find_article_link(archive_url, current_date)
        
        if not article_url:
            logger.warning(f"No AI News article found for {current_date.strftime('%Y-%m-%d')}")
            return None
        
        # Create temporary file for content
        with tempfile.NamedTemporaryFile(delete=False, mode='w', encoding='utf-8') as temp_file:
            temp_filename = temp_file.name
        
        # Scrape content between markers
        scrape_content(
            article_url,
            '<h1 id="ai-twitter-recap">AI Twitter Recap</h1>',
            'PART 1: High level Discord summaries',
            temp_filename
        )
        
        # Read the content from the temp file
        try:
            with open(temp_filename, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Clean up the temporary file
            os.unlink(temp_filename)
            
            # Return the content as a dictionary
            return {
                'title': f"AI News for {current_date.strftime('%Y-%m-%d')}",
                'link': article_url,
                'snippet': content[:500] + ('...' if len(content) > 500 else ''),
                'content': content,
                'source': "buttondown.com/ainews"
            }
            
        except Exception as e:
            logger.error(f"Error reading scraped content: {str(e)}")
            
            # Clean up the temporary file if it exists
            if os.path.exists(temp_filename):
                os.unlink(temp_filename)
            
            return None
        
    except Exception as e:
        logger.error(f"Error scraping AI News: {str(e)}")
        return None

def find_article_link(archive_url, target_date):
    """
    Find the article link for a specific date from the archive page.
    
    Args:
        archive_url (str): The URL of the archive page
        target_date (datetime): The target date to find
        
    Returns:
        str: Article URL or None if not found
    """
    try:
        # Fetch the archive page
        response = requests.get(archive_url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch the archive page. Status code: {response.status_code}")
            return None
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all email divs
        email_divs = soup.find_all('div', class_='email')
        
        # Format the target date as it appears in the page (e.g., "March 7, 2025")
        target_date_str = target_date.strftime("%B %d, %Y").replace(" 0", " ")  # Remove leading zero
        
        # Look for the link with the matching date
        for email in email_divs:
            metadata = email.find('div', class_='email-metadata')
            if metadata and target_date_str in metadata.get_text(strip=True):
                link = email.find_parent('a')
                if link and 'href' in link.attrs:
                    logger.info(f"Found article for {target_date_str}: {link['href']}")
                    return link['href']
        
        logger.warning(f"No article found for {target_date_str}")
        return None
        
    except Exception as e:
        logger.error(f"Error finding article link: {str(e)}")
        return None

def scrape_content(url, start_marker, end_marker, output_file):
    """
    Scrape content between two markers and save to a file.
    
    Args:
        url (str): The URL to scrape
        start_marker (str): The HTML marker to start capturing from
        end_marker (str): The text marker to stop capturing at
        output_file (str): The file to save content to
    """
    try:
        # Fetch the webpage content
        response = requests.get(url)
        if response.status_code != 200:
            logger.error(f"Failed to fetch the article page. Status code: {response.status_code}")
            return
        
        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find the starting point
        start_element = soup.find('h1', id='ai-twitter-recap')
        if not start_element:
            logger.error("Start marker 'AI Twitter Recap' not found.")
            return
        
        # Collect content until the end marker
        content = []
        current_element = start_element
        found_end = False
        
        # Add the start element itself
        content.append(str(current_element))
        
        # Iterate through subsequent siblings
        while current_element.next_sibling and not found_end:
            current_element = current_element.next_sibling
            element_str = str(current_element).strip()
            if element_str:
                if end_marker in element_str:
                    found_end = True
                    break
                content.append(element_str)
        
        if not found_end:
            logger.warning("End marker not found. Content may be incomplete.")
        
        # Join the content and write to file
        full_content = '\n'.join(content)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(full_content)
        
        logger.info(f"Content successfully saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Error scraping content: {str(e)}")