import os
import re

html_files = [f for f in os.listdir('.') if f.endswith('.html')]

links_map = [
    # Sidebar links
    (r'<a[^>]+href="[^"]*"[^>]*>\s*<span[^>]*>dashboard</span>\s*<span[^>]*>Dashboard</span>\s*</a>', 
     r'<a href="user_dashboard.html" class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"> <span class="material-symbols-outlined text-xl">dashboard</span> <span class="text-sm font-medium">Dashboard</span> </a>'),
    
    (r'<a[^>]+href="[^"]*"[^>]*>\s*<span[^>]*>settings</span>\s*<span[^>]*>(?:System Preferences|Settings)</span>\s*</a>',
     r'<a href="settings.html" class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"> <span class="material-symbols-outlined text-xl">settings</span> <span class="text-sm font-medium">Settings</span> </a>'),
    
    (r'<a[^>]+href="[^"]*"[^>]*>\s*<span[^>]*>help</span>\s*<span[^>]*>Help Center</span>\s*</a>',
     r'<a href="help_center.html" class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"> <span class="material-symbols-outlined text-xl">help</span> <span class="text-sm font-medium">Help Center</span> </a>'),
    
    (r'<a[^>]+href="[^"]*"[^>]*>\s*<span[^>]*>logout</span>\s*<span[^>]*>Logout</span>\s*</a>',
     r'<a href="index.html" class="flex items-center gap-3 px-3 py-2.5 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors text-red-500"> <span class="material-symbols-outlined text-xl">logout</span> <span class="text-sm font-medium">Logout</span> </a>'),

    # Header / Main links that might just say "Login", "Sign Up", "Logout"
    (r'href="#"([^>]*>Login)', r'href="login.html"\1'),
    (r'href="#"([^>]*>Sign Up)', r'href="signup.html"\1'),
    (r'href="#"([^>]*>Get Started)', r'href="signup.html"\1'),
    (r'href="#"([^>]*>Dashboard)', r'href="user_dashboard.html"\1'),
    (r'href="#"([^>]*>Logout)', r'href="index.html"\1'),
]

for file in html_files:
    with open(file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    # Replace sidebar anchor links if they match structure
    # Wait, earlier they were DIVs. Let me convert the DIVs properly first before applying python regex
    
    # Simple replace for common buttons:
    content = re.sub(r'href="[^"]*"([^>]*>\s*Login\s*<)', r'href="login.html"\1', content, flags=re.IGNORECASE)
    content = re.sub(r'href="[^"]*"([^>]*>\s*Sign Up\s*<)', r'href="signup.html"\1', content, flags=re.IGNORECASE)
    content = re.sub(r'href="[^"]*"([^>]*>\s*Get Started\s*<)', r'href="signup.html"\1', content, flags=re.IGNORECASE)
    
    # Dashboard redirect after login/signup
    content = re.sub(r'(<button[^>]*>)\s*Sign In\s*(</button>)', r'<a href="user_dashboard.html" style="display:inline-block;width:100%;">\1Sign In\2</a>', content, flags=re.IGNORECASE)
    content = re.sub(r'(<button[^>]*>)\s*Create Account\s*(</button>)', r'<a href="user_dashboard.html" style="display:inline-block;width:100%;">\1Create Account\2</a>', content, flags=re.IGNORECASE)

    # Let's fix the DIV to A conversion for Sidebars (Dashboard, Settings, Help Center)
    
    div_pattern = re.compile(r'<div([^>]*class="[^"]*cursor-pointer[^"]*"[^>]*)>\s*<span[^>]*>([a-z_]+)</span>\s*<span[^>]*>([^<]+)</span>\s*</div>', re.IGNORECASE)
    
    def replacer(match):
        attrs = match.group(1)
        icon = match.group(2)
        text = match.group(3)
        
        target = "#"
        if icon == "settings":
            target = "settings.html"
        elif icon == "help":
            target = "help_center.html"
        elif icon == "dashboard":
            target = "user_dashboard.html"
        elif icon == "logout":
            target = "index.html"
        
        # if it's not one of the navigation items we know, keep it as div
        if target == "#":
            return match.group(0)
            
        return f'<a href="{target}"{attrs}>\n<span class="material-symbols-outlined text-[22px]">{icon}</span>\n<span class="text-sm font-medium">{text}</span>\n</a>'
        
    content = div_pattern.sub(replacer, content)

    # Convert existing anchor links in Sidebars to point correct
    content = re.sub(r'<a([^>]+)href="[^"]*"([^>]*)>\s*<span([^>]+)>settings</span>\s*<span([^>]+)>([^<]*)</span>\s*</a>', 
                     r'<a\1href="settings.html"\2>\n<span\3>settings</span>\n<span\4>\5</span>\n</a>', content, flags=re.IGNORECASE)
                     
    content = re.sub(r'<a([^>]+)href="[^"]*"([^>]*)>\s*<span([^>]+)>help</span>\s*<span([^>]+)>([^<]*)</span>\s*</a>', 
                     r'<a\1href="help_center.html"\2>\n<span\3>help</span>\n<span\4>\5</span>\n</a>', content, flags=re.IGNORECASE)
                     
    content = re.sub(r'<a([^>]+)href="[^"]*"([^>]*)>\s*<span([^>]+)>dashboard</span>\s*<span([^>]+)>([^<]*)</span>\s*</a>', 
                     r'<a\1href="user_dashboard.html"\2>\n<span\3>dashboard</span>\n<span\4>\5</span>\n</a>', content, flags=re.IGNORECASE)
                     
    content = re.sub(r'<a([^>]+)href="[^"]*"([^>]*)>\s*<span([^>]+)>logout</span>\s*<span([^>]+)>([^<]*)</span>\s*</a>', 
                     r'<a\1href="index.html"\2>\n<span\3>logout</span>\n<span\4>\5</span>\n</a>', content, flags=re.IGNORECASE)

    if content != original_content:
        with open(file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {file}")

print("Done")
