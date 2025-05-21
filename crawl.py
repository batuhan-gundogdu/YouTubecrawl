from googleapiclient.discovery import build 
from datetime import datetime, timedelta
import pytz
import csv
import os

# === OUTPUT Configuration === 
def setup_output_path():
    # Define output directory
    output_dir = os.getenv('YOUTUBE_CRAWL_OUTPUT_DIR', '.')

    # Make sure the output directory exists
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Build output file path
    output_file = os.path.join(output_dir, 'youtube_comments.csv')
    
    # Confirm where we're writing
    print(f"🔍 Writing to: {os.path.abspath(output_file)}")
    return output_file

# Call the setup function and store the file path
output_file = setup_output_path()


API_KEY = 'AIzaSyBSGCVxqEyuA91onBHKPQg5W9JiDXRwaU0'
CHANNEL_ID = 'UCIVk1L1-JmpdiGuZcVjImtA'  # ABC15 Arizona Channel ID

youtube = build('youtube', 'v3', developerKey=API_KEY)

def get_recent_videos(channel_id, days=7):
    published_after = (datetime.now(pytz.UTC) - timedelta(days=days)).isoformat()
    videos = []
    
    request = youtube.search().list(
        part="id,snippet",
        channelId=channel_id,
        maxResults=50,
        order="date",
        publishedAfter=published_after
    )
    response = request.execute()
    
    for item in response.get('items', []):
        if item['id']['kind'] == 'youtube#video':
            videos.append({
                'videoId': item['id']['videoId'],
                'title': item['snippet']['title'],
                'publishedAt': item['snippet']['publishedAt']
            })
    return videos


def get_comments(video_id):
    comments = []
    try:
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=100,
            textFormat="plainText"
        )
        response = request.execute()
        
        for item in response.get('items', []):
            # Define top-level comment and user ID here
                top_snippet = item['snippet']['topLevelComment']['snippet']
                top_comment = top_snippet['textDisplay']
                top_user_id = top_snippet.get('authorChannelId', {}).get('value', 'UNKNOWN_USER')
            
            # Store comment + user
                comment_entry = {
                    'comment': top_comment,
                    'user_id': top_user_id,
                    'replies': []
                }
            
            # Handle replies if they exist
                if 'replies' in item:
                    for reply in item['replies']['comments']:
                        reply_snippet = reply['snippet']
                        reply_text = reply_snippet['textDisplay']
                        reply_user_id = reply_snippet.get('authorChannelId', {}).get('value', 'UNKNOWN_USER')

                        comment_entry['replies'].append({
                            'text': reply_text,
                            'user_id': reply_user_id
                        })

                comments.append(comment_entry)

    except Exception as e:
        print(f"Error fetching comments for {video_id}: {e}")

    return comments   

# Main script
with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['date', 'title', 'user_id', 'comment'])
    videos = get_recent_videos(CHANNEL_ID)
    for video in videos:
        comments = get_comments(video['videoId'])
        for c in comments:
            # Write top-level comment
            writer.writerow([video['publishedAt'], video['title'], c['user_id'], c['comment']])
            # Write replies
            for reply in c['replies']:
                writer.writerow([video['publishedAt'], video['title'], reply['user_id'], reply['text']])


# End of your script
print(f"Crawl completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print(f"CSV saved to: {os.path.abspath(output_file)}")