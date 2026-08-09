import sys

js_path = r"c:\Users\syaki\Desktop\misinformation-detection-system\app\static\app.js"
with open(js_path, 'r', encoding='utf-8') as f:
    js = f.read()

# Replace toggleHistory
old_history = '''    function toggleHistory(force) {
        historyVisible = (force !== undefined) ? force : !historyVisible;
        historyPanel.classList.toggle("hidden", !historyVisible);
        const icon = btnToggleHistory.querySelector("i");
        icon.className = historyVisible ? "fa-solid fa-xmark" : "fa-solid fa-clock-rotate-left";
    }'''

new_history = '''    function toggleHistory(force) {
        historyVisible = (force !== undefined) ? force : !historyVisible;
        if (window.innerWidth <= 1024) {
            document.getElementById('history-sidebar').classList.toggle('mobile-open', historyVisible);
            document.getElementById('mobile-backdrop').classList.toggle('hidden', !historyVisible);
            if (historyVisible) {
                // Ensure aux is closed
                auxVisible = false;
                document.getElementById('aux-sidebar').classList.remove('mobile-open');
                const auxIcon = btnToggleAux.querySelector("i");
                if (auxIcon) auxIcon.className = "fa-solid fa-chart-line";
            }
        } else {
            document.getElementById('history-sidebar').classList.toggle("hidden", !historyVisible);
        }
        
        const icon = btnToggleHistory.querySelector("i");
        if (icon) icon.className = historyVisible ? "fa-solid fa-xmark" : "fa-solid fa-clock-rotate-left";
    }'''

js = js.replace(old_history, new_history)

# Replace toggleAux
old_aux = '''    function toggleAux(force) {
        auxVisible = (force !== undefined) ? force : !auxVisible;
        auxPanel.classList.toggle("hidden", !auxVisible);
        appLayout.classList.toggle("aux-active", auxVisible);
        const icon = btnToggleAux.querySelector("i");
        icon.className = auxVisible ? "fa-solid fa-xmark" : "fa-solid fa-chart-line";
    }'''

new_aux = '''    function toggleAux(force) {
        auxVisible = (force !== undefined) ? force : !auxVisible;
        if (window.innerWidth <= 1024) {
            document.getElementById('aux-sidebar').classList.toggle('mobile-open', auxVisible);
            document.getElementById('mobile-backdrop').classList.toggle('hidden', !auxVisible);
            if (auxVisible) {
                // Ensure history is closed
                historyVisible = false;
                document.getElementById('history-sidebar').classList.remove('mobile-open');
                const histIcon = btnToggleHistory.querySelector("i");
                if (histIcon) histIcon.className = "fa-solid fa-clock-rotate-left";
            }
        } else {
            document.getElementById('aux-sidebar').classList.toggle("hidden", !auxVisible);
            appLayout.classList.toggle("aux-active", auxVisible);
        }
        
        const icon = btnToggleAux.querySelector("i");
        if (icon) icon.className = auxVisible ? "fa-solid fa-xmark" : "fa-solid fa-chart-line";
    }'''

js = js.replace(old_aux, new_aux)

# Add backdrop click listener
if 'mobile-backdrop' not in js:
    backdrop_listener = '''
    // Mobile Backdrop click
    const mobileBackdrop = document.getElementById('mobile-backdrop');
    if (mobileBackdrop) {
        mobileBackdrop.addEventListener('click', () => {
            if (historyVisible) toggleHistory(false);
            if (auxVisible) toggleAux(false);
        });
    }
'''
    js = js.replace('// --- Event Listeners ---', '// --- Event Listeners ---\n' + backdrop_listener)
    js = js.replace('// 🛑 Event Listeners', '// 🛑 Event Listeners\n' + backdrop_listener)

with open(js_path, 'w', encoding='utf-8') as f:
    f.write(js)
