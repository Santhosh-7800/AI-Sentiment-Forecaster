import os
import re

html_files = [f for f in os.listdir('.') if f.endswith('.html')]

# We replace href="#" inside a block that contains specific text nearby 
# We'll use a simpler approach: replace entire <a> or <button> tag's href
def replace_links(match):
    full_tag = match.group(0)
    text = full_tag.lower()
    if 'dashboard' in text: return full_tag.replace('#', 'user_dashboard.html')
    if 'settings' in text: return full_tag.replace('#', 'settings.html')
    if 'help' in text or 'docs' in text or 'community' in text or 'updates' in text: return full_tag.replace('#', 'help_center.html')
    if 'market trends' in text: return full_tag.replace('#', 'market_trends.html')
    if 'reports' in text: return full_tag.replace('#', 'reports.html')
    if 'sentiment' in text: return full_tag.replace('#', 'sentiment_analysis.html')
    if 'login' in text or 'sign in' in text: return full_tag.replace('#', 'login.html')
    if 'sign up' in text or 'get started' in text or 'create account' in text: return full_tag.replace('#', 'signup.html')
    if 'logout' in text: return full_tag.replace('#', 'index.html')
    if 'admin' in text: return full_tag.replace('#', 'admin_panel.html')
    if 'profile' in text: return full_tag.replace('#', 'settings.html#profile')
    if 'security' in text: return full_tag.replace('#', 'settings.html#security')
    if 'notifications' in text: return full_tag.replace('#', 'settings.html#notifications')
    if 'billing' in text: return full_tag.replace('#', 'settings.html#billing')
    if 'trendai' in text: return full_tag.replace('#', 'index.html')
    return full_tag

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Match <a href="#">...</a>
    # Or <a class="..." href="#">...</a>
    # non-greedy everything up to </a>
    pattern = re.compile(r'<a\s+[^>]*href="#"[^>]*>.*?</a>', re.IGNORECASE | re.DOTALL)
    
    new_content = pattern.sub(replace_links, content)
    
    if new_content != content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file}")

print("Done connecting links!")
