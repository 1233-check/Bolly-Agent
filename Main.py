import feedparser
import tweepy
import google.generativeai as genai
import time
import random
import logging
import sys
from datetime import datetime
import os 
import json # NEW: Used to save and load post history

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

# --- HISTORY MANAGEMENT CONSTANTS ---
HISTORY_FILE = "post_history.json"
MAX_HISTORY = 5 # Tracks the last 5 unique posts to avoid immediate duplicates
# ------------------------------------

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
# 3. CORE FUNCTIONS
# ==========================================
def get_twitter_conn():
    """Initializes the Twitter client using OAuth 1.0a (required for posting)"""
    # FIX: Corrected argument name for tweepy.Client (access_token_secret)
    return tweepy.Client(
        consumer_key=TWITTER_API_KEY, 
        consumer_secret=TWITTER_API_SECRET,
        access_token=ACCESS_TOKEN, 
        access_token_secret=ACCESS_SECRET 
    )

def get_bolly_news():
    """Fetches the newest story (index 0) from RSS."""
    logging.info("🍿 Checking RSS feed for new gossip...")
    try:
        feed = feedparser.parse(RSS_URL)
        if feed.entries:
            # FIX: Prioritizes the absolute newest story (index 0)
            story = feed.entries[0] 
            logging.info(f"Found Story: {story.title}")
            return story.title, f"Headline: {story.title}. Summary: {story.summary}"
    except Exception as e:
        logging.error(f"RSS Parsing Error: {e}")
    return None, None

# --- HISTORY MANAGEMENT FUNCTIONS ---

def load_history():
    """Loads the history of previously posted headlines from file."""
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, 'r') as f:
            try:
                # The file must be read within the persistent GitHub Actions workspace
                return json.load(f)
            except json.JSONDecodeError:
                # If the file is empty or corrupted, start fresh
                return []
    return []

def save_history(history, new_headline):
    """Adds new headline and truncates history file to MAX_HISTORY size."""
    history.insert(0, new_headline)
    
    if len(history) > MAX_HISTORY:
        history = history[:MAX_HISTORY] 
    
    with open(HISTORY_FILE, 'w') as f:
        # Writes the updated history back to the file
        json.dump(history, f)
    return history

# --- SEO AGENT FUNCTION ---
def generate_seo_keywords(news_context):
    """Generates high-engagement keywords and 2 trending hashtags."""
    logging.info("🧠 SEO Agent: Generating keywords and hashtags...")
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction="""
        You are an Expert SEO Analyst for Bollywood content. Your task is to analyze the given news context and output a list of exactly 5 high-traffic, high-engagement keywords/phrases and 2 trending hashtags.

        Output Format: A single string, with all items separated by commas.
        Example: Shah Rukh Khan, Jawan, Box Office, Atlee, Pathaan, #SRK, #Jawan
        """
    )
    response = model.generate_content(news_context)
    return response.text.strip()

# --- CREATIVE AGENT FUNCTION ---
def generate_tweet(news_context, seo_keywords):
    """Uses Gemini to write the optimized tweet with personality."""
    logging.info("✍️ Creative Agent: Writing optimized tweet...")
    
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash", 
        system_instruction=f"""
        You are a viral Bollywood Twitter influencer. 
        Task: Rewrite the provided news into a dramatic, sarcastic Hinglish tweet. You MUST naturally integrate the provided keywords and hashtags to maximize reach.

        Keywords to integrate: {seo_keywords}
        
        Rules:
        - Must mix Hindi and English (Hinglish slang is mandatory).
        - Use dramatic words like: 'Bawal', 'Scene', 'Queen', 'Khatam'.
        - Keep the total length under 280 characters.
        - The hashtags must be placed logically at the end of the tweet.
        """
    )
    response = model.generate_content(news_context)
    return response.text.strip()


# ==========================================
# 4. THE SELF-HEALING LOOP (24/7)
# ==========================================
def run_bot():
    logging.info("--- BOLLYWOOD BOT INITIATING (FRESHNESS CHECK ENABLED) ---")
    
    # Initialize Twitter client (will crash if keys are invalid)
    try:
        client = get_twitter_conn()
    except Exception as e:
        logging.critical(f"FATAL: Twitter Client Initialization Failed: {e}")
        # Allows GitHub Actions to report a definitive failure
        raise

    while True:
        try:
            # 1. LOAD HISTORY
            post_history = load_history()
            
            # 2. GET LATEST NEWS
            latest_headline, news_context = get_bolly_news()
            
            if news_context:
                # 3. CHECK FOR DUPLICATES
                if latest_headline in post_history:
                    logging.warning(f"⏰ Story is old/duplicate: '{latest_headline}'. Skipping cycle.")
                    
                else:
                    # 4. SEO STAGE
                    seo_keywords = generate_seo_keywords(news_context)
                    logging.info(f"🔑 SEO Keywords: {seo_keywords}")

                    # 5. CREATIVE STAGE
                    tweet = generate_tweet(news_context, seo_keywords)
                    logging.info(f"📝 Final Optimized Draft: {tweet}")
                    
                    # Final Safety Check
                    if len(tweet) > 280:
                        tweet = tweet[:277] + "..."
                    
                    # 6. POST
                    client.create_tweet(text=tweet)
                    logging.info("✅ TWEET POSTED SUCCESSFULLY!")
                    
                    # 7. UPDATE HISTORY
                    save_history(post_history, latest_headline)

            else:
                logging.warning("❌ No fresh gossip found on this cycle.")

            # --- SLEEP (4 hours +/- 15 mins) ---
            sleep_seconds = 12600 + random.randint(-900, 900)
            
            wake_up_time = datetime.fromtimestamp(datetime.now().timestamp() + sleep_seconds).strftime('%H:%M:%S')
            logging.info(f"💤 Sleeping for {sleep_seconds/60:.0f} mins. Next post approx: {wake_up_time}")
            time.sleep(sleep_seconds)

        # --- SELF-HEALING LOGIC ---
        except tweepy.errors.TooManyRequests:
            logging.error("⛔ RATE LIMIT HIT. Waiting 30 mins to heal (1800s)...")
            time.sleep(1800)
            
        except tweepy.errors.Unauthorized:
            logging.critical("⛔ INVALID KEYS. Please check your Access Token/Secret. Stopping.")
            break
            
        except Exception as e:
            logging.error(f"⚠️ UNHANDLED CRASH: {e}")
            logging.info("🩹 Applying self-healing... Restarting loop in 5 minutes (300s).")
            time.sleep(300)

if __name__ == "__main__":
    run_bot()
