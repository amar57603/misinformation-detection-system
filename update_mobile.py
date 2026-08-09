import sys

html_path = r"c:\Users\syaki\Desktop\misinformation-detection-system\app\static\index.html"
with open(html_path, 'r', encoding='utf-8') as f:
    html = f.read()
if 'id="mobile-backdrop"' not in html:
    html = html.replace('<body>', '<body>\n    <div id="mobile-backdrop" class="mobile-backdrop hidden"></div>')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)

css_path = r"c:\Users\syaki\Desktop\misinformation-detection-system\app\static\style.css"
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

if 'mobile-backdrop' not in css:
    css += '''
/* Mobile Sliding Panels CSS */
.mobile-backdrop {
    position: fixed; inset: 0; background: rgba(0, 0, 0, 0.5); backdrop-filter: blur(4px);
    z-index: 1999; opacity: 1; transition: opacity 0.3s ease, visibility 0.3s;
}
.mobile-backdrop.hidden { opacity: 0; visibility: hidden; pointer-events: none; }

@media (max-width: 1024px) {
    .sidebar {
        position: fixed; top: 0; left: 0; bottom: 0;
        width: 85%; max-width: 320px; z-index: 2000;
        transform: translateX(-100%); transition: transform 0.3s ease;
        display: flex !important; /* override hidden */
    }
    .sidebar.mobile-open { transform: translateX(0); }
    
    .aux-panel {
        position: fixed; top: 0; right: 0; bottom: 0;
        width: 85%; max-width: 350px; z-index: 2000;
        transform: translateX(100%); transition: transform 0.3s ease;
        display: flex !important; /* override hidden */
    }
    .aux-panel.mobile-open { transform: translateX(0); }
}
'''
    with open(css_path, 'w', encoding='utf-8') as f:
        f.write(css)
