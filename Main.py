import feedparser
import tweepy
import google.generativeai as genai
import time
import random
import logging
import sys
from datetime import datetime
import os 
# os is imported to read environment variables (GitHub Secrets)

# ==========================================
# 1. CONFIGURATION (READ FROM ENVIRONMENT)
# ==========================================
# Keys are securely read from GitHub Secrets. The names must match the secrets created.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TWITTER_API_KEY = os.environ.get("TWITTER_API_KEY")
TWITTER_API_SECRET = os.environ.get("TWITTER_API_SECRET")
ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN")
ACCESS_SECRET = os.environ.get("ACCESS_SECRET")

# RSS Feed for Bollywood News (Google News India - High Traffic)
RSS_URL = "https://news.google.com/rss/search?q=Bollywood+gossip+OR+Box+Office+India+OR+Indian+Film+Celebrity&hl=en-IN&gl=IN&ceid=IN:en"

# ==========================================
# 2. SETUP & LOGGING
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot_log.txt"),
        logging.StreamHandler(sys.stdout)
    ]
)

# Initialize Gemini API configuration
genai.configure(api_key=GEMINI_API_KEY)

# ==========================================
# 3. INTELLIGENCE FUNCTIONS
# ==========================================
def get_twitter_conn():
    """Initializes the Twitter client using OAuth 1.0a (required for posting)"""
    # FIX APPLIED: Corrected 'access_secret' keyword to 'access_token_secret'
    return tweepy.Client(
        consumer_key=TWITTER_API_KEY, 
        consumer_secret=TWITTER_API_SECRET,
        access_token=ACCESS_TOKEN, 
        access_token_secret=ACCESS_SECRET 
    )

def get_bolly_news():
    """Fetches a random top story from RSS"""
    logging.info("🍿 Checking RSS feed for new gossip...")
    try:
        feed = feedparser.parse(RSS_URL)
        if feed.entries:
            # Pick one random story from top 7 for unique timing
            story = random.choice(feed.entries[:7]) 
            logging.info(f"Found Story: {story.title}")
            return f"Headline: {story.title}. Summary: {story.summary}"
    except Exception as e:
        logging.error(f"RSS Parsing Error: {e}")
    return None

def generate_tweet(news_context):
    """Uses Gemini to write the tweet with personality"""
    # FIX APPLIED: Changed model name to stable 'gemini-2.5-flash' to avoid 400 error
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction="""
        You are a viral Bollywood Twitter influencer. 
        Task: Rewrite the provided news into a dramatic, sarcastic Hinglish tweet.
        
        Rules:
        - Must mix Hindi and English (Hinglish slang is mandatory).
        - Use dramatic words like: 'Bawal', 'Scene', 'Bhai', 'Queen', 'Flop', 'Blockbuster', 'Khatam'.
        - NO hashtags.
        - Max 280 characters.
        - Be controversial or highly supportive to spark engagement.
        """
    )
    response = model.generate_content(news_context)
    return response.text.strip()

# ==========================================
# 4. THE SELF-HEALING LOOP (24/7)
# ==========================================
def run_bot():
    logging.info("--- BOLLYWOOD BOT INITIATING ---")
    
    # Initialize Twitter client (will crash immediately if keys are wrong)
    try:
        client = get_twitter_conn()
    except Exception as e:
        logging.critical(f"FATAL: Twitter Client Initialization Failed: {e}")
        logging.critical("Check your 4 Twitter API/Access keys and the 'Read and Write' permissions.")
        # Re-raise the error to let GitHub Actions fail clearly
        raise

    while True:
        try:
            # --- ACTION PHASE ---
            news = get_bolly_news()
            
            if news:
                tweet = generate_tweet(news)
                logging.info(f"📝 Generated Draft: {tweet}")
                
                # Final Safety Check
                if len(tweet) > 280:
                    tweet = tweet[:277] + "..."
                
                # POST
                client.create_tweet(text=tweet)
                logging.info("✅ TWEET POSTED SUCCESSFULLY!")
                
            else:
                logging.warning("❌ No fresh gossip found on this cycle.")

            # --- SLEEP (Post 6-7 times a day) ---
            sleep_seconds = 12600 + random.randint(-900, 900)
            
            wake_up_time = datetime.fromtimestamp(datetime.now().timestamp() + sleep_seconds).strftime('%H:%M:%S')
            logging.info(f"💤 Sleeping for {sleep_seconds/60:.0f} mins. Next post approx: {wake_up_time}")
            time.sleep(sleep_seconds)

        # --- AI ERROR HANDLING (SELF-HEAL) ---
        except tweepy.errors.TooManyRequests:
            # Rate Limit Error (429): Pause for a long time
            logging.error("⛔ RATE LIMIT HIT. Waiting 30 mins to heal (1800s)...")
            time.sleep(1800)
            
        except tweepy.errors.Unauthorized:
            # Token Error: Fatal, requires manual key fix
            logging.critical("⛔ INVALID KEYS. Please check your Access Token/Secret. Stopping.")
            break
            
        except Exception as e:
            # General Crash: Log and attempt restart
            logging.error(f"⚠️ UNHANDLED CRASH: {e}")
            logging.info("🩹 Applying self-healing... Restarting loop in 5 minutes (300s).")
            time.sleep(300)

if __name__ == "__main__":
    run_bot()
