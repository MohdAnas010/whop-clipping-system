"""Stealth Agent - AI detection se bachne ke liye content ko human-like banata hai.

Instagram/YouTube AI-generated content detect karte hain:
1. Repetitive patterns (same hooks, same structure)
2. Robotic captions (perfect grammar, no personality)
3. Synthetic visuals (same template har video me)
4. Posting patterns (exact same time, no variation)

Ye agent har video ko unique banata hai:
- Hook variations (har baar naya angle)
- Natural imperfections (casual language, contractions)
- Visual variety (colors, pacing, text position me variation)
- Human-like posting (time me thoda random offset)
"""
import random

# Hook style variations - har video me alag style
HOOK_STYLES = [
    "question",      # "Ever wondered how..."
    "shocking",      # "Nobody talks about this..."
    "story",         # "Last month I found..."
    "direct",        # "Stop doing this..."
    "curiosity",     # "The secret behind..."
]

# Caption personality variations
CAPTION_VARIANTS = [
    "casual",    # lowercase, emojis, relaxed
    "pro",       # clean, professional
    "hype",      # energetic, exclamation
]

def humanize_script(script):
    """Script me human-like variation add karo."""
    style = random.choice(HOOK_STYLES)
    hook = script.get("hook", "")

    # Hook ko style ke hisaab se thoda modify karo (original meaning same)
    prefixes = {
        "question": "Quick question: ",
        "shocking": "Honestly, ",
        "story": "So here's the thing - ",
        "direct": "Listen, ",
        "curiosity": "Here's what nobody tells you: ",
    }
    if style in prefixes and not hook.lower().startswith(prefixes[style].strip().lower()[:4]):
        # Sirf kabhi-kabhi prefix add karo (har baar nahi - pattern avoid)
        if random.random() < 0.4:
            hook = prefixes[style] + hook[0].lower() + hook[1:] if hook else hook

    # Visual variety - har render me alag accent color
    accent_colors = ["#00ff88", "#ff6b6b", "#4ecdc4", "#ffe66d", "#a8e6cf", "#ff9ff3"]
    accent = random.choice(accent_colors)

    # Caption me personality
    caption = script.get("caption", "")
    variant = random.choice(CAPTION_VARIANTS)
    if variant == "casual" and random.random() < 0.5:
        caption = caption + " \U0001f525"  # fire emoji, kabhi-kabhi

    return {
        **script,
        "hook": hook,
        "caption": caption,
        "accentColor": accent,
        "stealth_style": style,
    }

def posting_offset_minutes():
    """Human-like posting: exact time se ±15 min random offset."""
    return random.randint(-15, 15)

def run(scripts):
    print(f"[stealth] {len(scripts)} scripts ko human-like bana rahe hain...")
    return [{**item, "script": humanize_script(item["script"])} for item in scripts]
