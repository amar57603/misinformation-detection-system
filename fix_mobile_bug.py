import sys

js_path = r"c:\Users\syaki\Desktop\misinformation-detection-system\app\static\app.js"
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Fix the IDs used in the mobile toggle logic
js = js.replace("document.getElementById('history-sidebar')", "document.getElementById('history-panel')")
js = js.replace("document.getElementById('aux-sidebar')", "document.getElementById('aux-panel')")

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)

css_path = r"c:\Users\syaki\Desktop\misinformation-detection-system\app\static\style.css"
with open(css_path, 'r', encoding='utf-8') as f:
    css = f.read()

# Fix the class name used in mobile CSS
css = css.replace(".sidebar {", ".history-panel {")
css = css.replace(".sidebar.mobile-open", ".history-panel.mobile-open")

# Also ensure history-panel has a background on mobile, because it's just a div inside result-panel
# normally it inherits background or relies on result-panel, but as a fixed drawer it needs its own background
# Let's inject a background to it for mobile
if "background: var(--bg-panel);" not in css.split("@media (max-width: 1024px)")[1]:
    css = css.replace(".history-panel {\n        position: fixed;", ".history-panel {\n        position: fixed;\n        background: var(--bg-panel);\n        border-right: 1px solid var(--border-color);")
    css = css.replace(".aux-panel {\n        position: fixed;", ".aux-panel {\n        position: fixed;\n        background: var(--bg-panel);\n        border-left: 1px solid var(--border-color);")

with open(css_path, 'w', encoding='utf-8') as f:
    f.write(css)
