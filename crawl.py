from googleapiclient.discovery import build
from datetime import datetime, timedelta
import pytz
import csv

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
    request = youtube.commentThreads().list(
        part="snippet,replies",
        videoId=video_id,
        maxResults=100,
        textFormat="plainText"
    )
    response = request.execute()
    
    for item in response.get('items', []):
        top_comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
        replies = []
        if 'replies' in item:
            for reply in item['replies']['comments']:
                replies.append(reply['snippet']['textDisplay'])
        comments.append({'comment': top_comment, 'replies': replies})
    
    return comments

# Main script
with open('youtube_comments.csv', 'w', newline='', encoding='utf-8') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['date', 'title', 'comment'])
    videos = get_recent_videos(CHANNEL_ID)
    for video in videos:
        comments = get_comments(video['videoId'])
        for c in comments:
            # Write top-level comment
            writer.writerow([video['publishedAt'], video['title'], c['comment']])
            # Write replies as if they are comments
            for reply in c['replies']:
                writer.writerow([video['publishedAt'], video['title'], reply])