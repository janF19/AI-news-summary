import os
import feedparser
from datetime import datetime, timezone
import logging

logger = logging.getLogger("daily_feed")

def get_feed_entries(current_date):
    """
    Parse feeds from sources.txt and return entries for the current date.
    
    Args:
        current_date (datetime): The date to filter entries by
        
    Returns:
        list: List of dictionaries containing feed entries
    """
    # Check if sources.txt exists
    if not os.path.exists('sources.txt'):
        logger.error("sources.txt file not found")
        return []
    
    # Load sources from sources.txt
    try:
        with open('sources.txt', 'r') as f:
            sources = [line.strip().split(' ', 1) for line in f if line.strip()]
            sources = [{'type': s[0], 'url': s[1]} for s in sources]
    except Exception as e:
        logger.error(f"Error reading sources.txt: {str(e)}")
        return []
    
    # Format current date for comparison
    current_date_str = current_date.strftime('%Y-%m-%d')
    
    # Storage for entries
    entries = []
    
    # Process each RSS/Atom feed
    for source in sources:
        if source['type'] in ['rss', 'atom']:
            logger.info(f"Processing {source['type']} feed: {source['url']}")
            
            try:
                feed = feedparser.parse(source['url'])
                
                if not feed.entries:
                    logger.warning(f"No entries found in feed: {source['url']}")
                    continue
                
                # Count matching entries for better logging
                matching_entries = 0
                total_entries = len(feed.entries)
                
                # Process all entries, not just the first one
                for entry in feed.entries:
                    # Extract date from the entry
                    entry_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        entry_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                    elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                        entry_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
                    elif 'published' in entry:
                        try:
                            entry_date = datetime.strptime(entry.published, '%a, %d %b %Y %H:%M:%S %z')
                        except ValueError:
                            try:
                                entry_date = datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
                            except ValueError:
                                pass
                    
                    if not entry_date:
                        logger.warning(f"Could not determine date for entry: {entry.get('title', 'Untitled')}")
                        continue
                    
                    # Check if the entry is from today
                    entry_date_str = entry_date.strftime('%Y-%m-%d')
                    if entry_date_str != current_date_str:
                        # Skip verbose logging for each skipped entry
                        continue
                    
                    matching_entries += 1
                    
                    # Extract content
                    content = entry.get('content', [{}])[0].get('value', '') if 'content' in entry else ''
                    if not content:
                        content = entry.get('description', '')
                    if not content:
                        content = entry.get('summary', 'No content available')
                    
                    # Extract link
                    link = entry.get('link', '')
                    
                    # Add to entries list with 'snippet' key instead of 'content'
                    entries.append({
                        'title': entry.get('title', 'Untitled'),
                        'link': link,
                        'snippet': content,
                        'source': source['url'],
                        'source_type': source['type'],
                        'date': entry_date
                    })
                    
                    logger.info(f"Added entry: {entry.get('title', 'Untitled')}")
                
                # Log summary instead of each skipped entry
                logger.info(f"Found {matching_entries} entries from {current_date_str} out of {total_entries} total entries")
                
            except Exception as e:
                logger.error(f"Error processing feed {source['url']}: {str(e)}")
    
    return entries