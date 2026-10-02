import os
import re

frontend_dir = os.path.join(os.getcwd(), 'frontend')
static_dir = os.path.join(frontend_dir, 'static')
screens_dir = os.path.join(static_dir, 'screens')
shared_dir = os.path.join(static_dir, 'shared')

# 1. Move shared and screens to frontend root
os.rename(shared_dir, os.path.join(frontend_dir, 'shared'))

screens = os.listdir(screens_dir)
for screen in screens:
    os.rename(os.path.join(screens_dir, screen), os.path.join(frontend_dir, screen))

os.rmdir(screens_dir)
os.rmdir(static_dir)

# 2. Update files in shared
for file in os.listdir(os.path.join(frontend_dir, 'shared')):
    file_path = os.path.join(frontend_dir, 'shared', file)
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Update navigation links from /route/ to ../route/ in core.js if needed
    # But core.js uses absolute paths in JS: `window.location.href = "/dashboard/";`
    content = re.sub(r'window\.location\.href = "(/[^/]+/)";', r'window.location.href = "..\1";', content)
    
    with open(file_path, 'w') as f:
        f.write(content)

# 3. Update files in screens
for screen in screens:
    screen_path = os.path.join(frontend_dir, screen)
    
    # HTML
    html_file = os.path.join(screen_path, 'index.html')
    if os.path.exists(html_file):
        with open(html_file, 'r') as f:
            content = f.read()
            
        content = content.replace(f'/static/screens/{screen}/styles.css', 'styles.css')
        content = content.replace(f'/static/screens/{screen}/script.js', 'script.js')
        content = content.replace('/static/shared/', '../shared/')
        
        # Replace navigation links: href="/dashboard/" -> href="../dashboard/"
        content = re.sub(r'href="/([a-z]+)/"', r'href="../\1/"', content)
        
        with open(html_file, 'w') as f:
            f.write(content)
            
    # JS
    js_file = os.path.join(screen_path, 'script.js')
    if os.path.exists(js_file):
        with open(js_file, 'r') as f:
            content = f.read()
            
        content = content.replace('/static/shared/', '../shared/')
        content = re.sub(r'window\.location\.href = "(/[^/]+/)";', r'window.location.href = "..\1";', content)
        
        with open(js_file, 'w') as f:
            f.write(content)

# 4. Update root index.html
index_file = os.path.join(frontend_dir, 'index.html')
with open(index_file, 'r') as f:
    content = f.read()
content = content.replace('url=/login/', 'url=./login/')
with open(index_file, 'w') as f:
    f.write(content)

print("Done")
