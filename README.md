🎬 Bolly-Agent: The Self-Healing, Viral Bollywood Twitter Bot

👑 The King of HYPE & Engagement

Bolly-Agent is an advanced, automated AI agent designed to dominate the Bollywood gossip space on X (Twitter). Unlike simple content bots, this agent uses a two-stage Gemini pipeline and robust self-healing logic to ensure maximum impressions while running 24/7 on the GitHub Actions free tier.

The goal is simple: achieve the 5 Million Impression mark required for X monetization by consistently posting trending, engagement-driven content in a natural, Hinglish voice.

🛠️ Core Architecture: The Two-Stage Brain

The agent runs in a pipeline to ensure quality, relevance, and SEO optimization.

Phase 1: The SEO Optimizing Agent (The Strategist)

Function: Reads the absolute freshest Bollywood news from Google News RSS (prioritizing the most recent story).

Goal: Generates a list of high-traffic keywords and 2 trending hashtags that are relevant to the story (e.g., #SRK, Box Office Bawal).

Phase 2: The Creative Agent (The Voice)

Model: Gemini 2.5 Flash

Function: Takes the raw headline and the SEO keywords, and transforms them into a dramatic, personalized, and slang-heavy Hinglish tweet designed to maximize clicks and replies (🔥 masala content).

🚨 Self-Healing & Freshness Protocol

The agent is designed for resilience and smart content delivery:

Feature

Description

Code Logic

Freshness Check

Prevents reposting old or duplicate headlines. The bot maintains a post_history.json and skips the cycle if the newest headline is already present.

if latest_headline in post_history: skip_cycle()

Self-Healing

If a network or API connection fails, the bot catches the error (try/except) and pauses for a short time (300s or 1800s) before automatically restarting the job.

except Exception as e: time.sleep(300)

Error Handling

Catches fatal 401/403 errors and logs them as CRITICAL, immediately stopping the job to prevent account lockouts.

except tweepy.errors.Unauthorized: break

⚙️ Deployment & Environment

This agent runs completely free of cost on GitHub Actions.

1. Environment Variables (Secrets)

All API keys are securely stored as Repository Secrets in GitHub. They must be set up correctly in your repository's Settings > Secrets and variables > Actions.

Secret Name

Purpose

Status

GEMINI_API_KEY

Provides access to the Gemini 2.5 Flash model.

✅ Set

TWITTER_API_KEY

X API Consumer Key.

✅ Set

TWITTER_API_SECRET

X API Consumer Secret.

✅ Set

ACCESS_TOKEN

User-specific token for posting.

✅ Set

ACCESS_SECRET

User-specific secret for posting.

✅ Set

2. Schedule

The bot runs on a cron schedule, configured in .github/workflows/schedule.yml.

Time

Frequency

cron: '0 0,4,8,12,16,20 * * *'

Runs 6 times daily (Every 4 hours UTC).

Goal: Get continuous exposure throughout the day.



❓ Troubleshooting: Common Deployment Errors

If the agent fails, look at the Actions log and check the error code.

Error Message

Cause

Resolution

python3: can't open file '.../main.py'

File Not Found. The capitalization in the workflow file is wrong.

Check the file list. If you see Main.py (Capital M), change the command in the YAML file to python3 Main.py.

TypeError: BaseClient.__init__...

Python Syntax Error. Incorrect argument name in the Twitter setup function.

FIXED IN CODE: Ensures access_token_secret is used instead of access_secret.

CRITICAL: 403 Forbidden

Policy Restriction. The X account's permissions are not correctly applied.

1. Go to X Developer Portal -> App Settings. 2. Verify permission is "Read and Write." 3. Regenerate your ACCESS_TOKEN and ACCESS_SECRET and update the GitHub Secrets immediately.

ERROR: UNHANDLED CRASH: 400 models/gemini-1.5...

Model Name Error. Deprecated model identifier used.

FIXED IN CODE: Changed model name to stable gemini-2.5-flash.
