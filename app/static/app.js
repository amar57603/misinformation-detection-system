document.addEventListener("DOMContentLoaded", () => {

    // ── UI Elements ──────────────────────────────────────────
    const textInput        = document.getElementById("news-text-input");
    const charCountEl      = document.getElementById("char-count");
    const wordCountEl      = document.getElementById("word-count");
    const btnPredict       = document.getElementById("btn-predict");
    const btnPaste         = document.getElementById("btn-paste");
    const btnClear         = document.getElementById("btn-clear");
    const btnToggleHistory = document.getElementById("btn-toggle-history");
    const btnClearHistory  = document.getElementById("btn-clear-history");
    const btnCopyResult    = document.getElementById("btn-copy-result");
    const btnThemeToggle   = document.getElementById("btn-theme-toggle");
    const themeIcon        = document.getElementById("theme-icon");

    // ── Theme Toggle ──────────────────────────────────────────
    const savedTheme = localStorage.getItem("siasatai_theme") || "dark";
    applyTheme(savedTheme);

    function applyTheme(theme) {
        if (theme === "light") {
            document.documentElement.setAttribute("data-theme", "light");
            themeIcon.className = "fa-solid fa-moon";
        } else {
            document.documentElement.removeAttribute("data-theme");
            themeIcon.className = "fa-solid fa-sun";
        }
        localStorage.setItem("siasatai_theme", theme);
    }

    btnThemeToggle.addEventListener("click", () => {
        const current = localStorage.getItem("siasatai_theme") || "dark";
        applyTheme(current === "dark" ? "light" : "dark");
    });

    const idlePlaceholder  = document.getElementById("idle-placeholder");
    const loaderSection    = document.getElementById("loader-section");
    const resultSection    = document.getElementById("result-section");
    const historyPanel     = document.getElementById("history-panel");
    const historyList      = document.getElementById("history-list");
    const historyCountEl   = document.getElementById("history-count");

    const verdictDisplay   = document.getElementById("verdict-display");
    const verdictIcon      = document.getElementById("verdict-icon");
    const verdictLabel     = document.getElementById("verdict-label");
    const confidenceText   = document.getElementById("confidence-percentage");
    const confidenceFill   = document.getElementById("confidence-fill");
    const statLang         = document.getElementById("stat-lang");
    const statWords        = document.getElementById("stat-words");
    const statModel        = document.getElementById("stat-model");
    const keywordsList     = document.getElementById("keywords-list");

    // ── State ─────────────────────────────────────────────────
    let history = JSON.parse(localStorage.getItem("siasatai_history") || "[]");
    let lastResult = null;
    let historyVisible = false;

    // ── Preset Texts ──────────────────────────────────────────
    const presets = {
        "bm-fake": "Awas! Virus baru yang disebarkan melalui udara kini sedang melanda beberapa kawasan perumahan. Sila sebarkan maklumat ini dengan segera sebelum terlambat dan elakkan keluar rumah tanpa tujuan penting!",
        "bm-real": "Kerajaan Malaysia telah meluluskan peruntukan sebanyak RM5 bilion dalam belanjawan negara bagi meningkatkan infrastruktur pengangkutan awam di seluruh negara. Projek ini meliputi pembinaan laluan LRT baharu, menaik taraf stesen komuter sedia ada, dan memperluaskan rangkaian bas ekspres antara negeri bagi memudahkan mobiliti rakyat.",
        "en-fake": "Amazing scientific secret! Drinking freshly squeezed lemon juice mixed with warm water every morning completely cures and protects you from all viral infections and flu. Share this post immediately with your friends and family to save lives!",
        "en-real": "Bank Negara Malaysia (BNM) announced that the Monetary Policy Committee has decided to maintain the Overnight Policy Rate (OPR) at 3.00 percent, citing stable domestic demand and moderate inflation levels in the national economy."
    };

    // ── Helpers ───────────────────────────────────────────────
    function updateCounters() {
        const text = textInput.value;
        charCountEl.textContent = text.length;
        const words = text.trim() === "" ? 0 : text.trim().split(/\s+/).length;
        wordCountEl.textContent = words;
    }

    function showToast(msg, icon = "fa-circle-check") {
        const existing = document.querySelector(".toast");
        if (existing) existing.remove();
        const t = document.createElement("div");
        t.className = "toast";
        t.innerHTML = `<i class="fa-solid ${icon}"></i> ${msg}`;
        document.body.appendChild(t);
        setTimeout(() => t.remove(), 2600);
    }

    function showState(state) {
        // state: "idle" | "loading" | "result"
        idlePlaceholder.classList.toggle("hidden", state !== "idle");
        loaderSection.classList.toggle("hidden", state !== "loading");
        resultSection.classList.toggle("hidden", state !== "result");

        // hide idle placeholder properly
        if (state === "idle") {
            idlePlaceholder.style.display = "flex";
        } else {
            idlePlaceholder.style.display = "none";
        }
    }

    // init
    showState("idle");

    // ── History ───────────────────────────────────────────────
    function saveHistory() {
        localStorage.setItem("siasatai_history", JSON.stringify(history));
    }

    function formatTime(iso) {
        const d = new Date(iso);
        return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) +
               " · " + d.toLocaleDateString([], { day: "2-digit", month: "short" });
    }

    function renderHistory() {
        historyCountEl.textContent = history.length;
        if (history.length === 0) {
            historyList.innerHTML = '<div class="history-empty">No history yet. Verify an article to begin.</div>';
            return;
        }
        historyList.innerHTML = "";
        [...history].reverse().forEach((item, idx) => {
            const el = document.createElement("div");
            el.className = "history-item";
            const isFake = item.prediction === "Fake";
            el.innerHTML = `
                <div class="history-item-top">
                    <span class="history-verdict ${isFake ? "fake" : "real"}">
                        ${isFake ? "⚠ Fake" : "✓ Real"}
                    </span>
                    <span class="history-confidence">${(item.confidence * 100).toFixed(1)}%</span>
                </div>
                <div class="history-preview">${item.text.substring(0, 100)}${item.text.length > 100 ? "…" : ""}</div>
                <div class="history-meta">
                    <span><i class="fa-solid fa-language"></i> ${item.language}</span>
                    <span><i class="fa-solid fa-font"></i> ${item.word_count} words</span>
                    <span><i class="fa-regular fa-clock"></i> ${formatTime(item.timestamp)}</span>
                </div>
            `;
            el.addEventListener("click", () => {
                textInput.value = item.text;
                updateCounters();
                toggleHistory(false);
                displayResults(item);
            });
            historyList.appendChild(el);
        });
    }

    function addToHistory(data) {
        const entry = { ...data, timestamp: new Date().toISOString() };
        history.push(entry);
        if (history.length > 50) history = history.slice(-50); // keep last 50
        saveHistory();
        renderHistory();
    }

    function toggleHistory(force) {
        historyVisible = (force !== undefined) ? force : !historyVisible;
        historyPanel.classList.toggle("hidden", !historyVisible);
        const icon = btnToggleHistory.querySelector("i");
        icon.className = historyVisible ? "fa-solid fa-xmark" : "fa-solid fa-clock-rotate-left";
    }

    // init history display
    renderHistory();

    // ── Event Listeners ───────────────────────────────────────
    textInput.addEventListener("input", updateCounters);

    // Paste button
    btnPaste.addEventListener("click", async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (text.trim()) {
                textInput.value = text;
                updateCounters();
                textInput.focus();
                showToast("Pasted from clipboard!", "fa-clipboard");
            } else {
                showToast("Clipboard is empty.", "fa-circle-exclamation");
            }
        } catch {
            showToast("Clipboard access denied. Paste manually (Ctrl+V).", "fa-circle-xmark");
        }
    });

    // Clear button
    btnClear.addEventListener("click", () => {
        textInput.value = "";
        updateCounters();
        showState("idle");
        lastResult = null;
        textInput.focus();
    });

    // History toggle
    btnToggleHistory.addEventListener("click", () => toggleHistory());

    // Clear history
    btnClearHistory.addEventListener("click", () => {
        history = [];
        saveHistory();
        renderHistory();
        showToast("History cleared.", "fa-trash-can");
    });

    // Copy/Share result
    btnCopyResult.addEventListener("click", () => {
        if (!lastResult) return;
        const isFake = lastResult.prediction === "Fake";
        const text = `[SiasatAI by DSG]\nVerdict: ${isFake ? "⚠ SUSPECTED FAKE" : "✓ CONFIRMED REAL"}\nConfidence: ${(lastResult.confidence * 100).toFixed(1)}%\nLanguage: ${lastResult.language}\n\nText: "${lastResult.text.substring(0, 200)}..."`;
        navigator.clipboard.writeText(text).then(() => {
            showToast("Result copied!", "fa-copy");
        }).catch(() => {
            showToast("Copy failed. Try again.", "fa-circle-xmark");
        });
    });

    // Preset buttons
    document.querySelectorAll(".preset-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            const key = btn.getAttribute("data-preset");
            if (presets[key]) {
                textInput.value = presets[key];
                updateCounters();
                btn.style.transform = "scale(0.97)";
                setTimeout(() => btn.style.transform = "", 150);
            }
        });
    });

    // ── Verify / Predict ──────────────────────────────────────
    btnPredict.addEventListener("click", async () => {
        const text = textInput.value.trim();
        const words = text === "" ? 0 : text.split(/\s+/).length;

        if (words < 3) {
            showToast("Please enter at least 3 words to analyze.", "fa-circle-exclamation");
            return;
        }

        showState("loading");
        btnPredict.disabled = true;

        try {
            const response = await fetch("/api/predict", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.detail || "API request failed.");
            }

            const data = await response.json();
            displayResults(data);
            addToHistory(data);

        } catch (error) {
            showState("idle");
            showToast(`Error: ${error.message}`, "fa-circle-xmark");
        } finally {
            btnPredict.disabled = false;
        }
    });

    // ── Display Results ───────────────────────────────────────
    function displayResults(data) {
        lastResult = data;
        showState("result");

        const isFake = data.prediction === "Fake";

        verdictDisplay.className = "verdict-display " + (isFake ? "state-fake" : "state-real");
        resultSection.className  = "result-card " + (isFake ? "state-fake" : "state-real");

        verdictLabel.textContent = isFake ? "SUSPECTED FAKE" : "CONFIRMED REAL";
        verdictIcon.className    = isFake ? "fa-solid fa-triangle-exclamation" : "fa-solid fa-circle-check";

        const pct = (data.confidence * 100).toFixed(1);
        confidenceText.textContent = `${pct}%`;
        // reset then animate
        confidenceFill.style.width = "0%";
        setTimeout(() => { confidenceFill.style.width = `${pct}%`; }, 50);

        statLang.textContent  = data.language;
        statWords.textContent = data.word_count;
        statModel.textContent = "LogReg (93.99%)";

        keywordsList.innerHTML = "";
        if (data.keywords_detected && data.keywords_detected.length > 0) {
            data.keywords_detected.forEach(word => {
                const badge = document.createElement("span");
                badge.className = "keyword-badge";
                badge.textContent = word;
                keywordsList.appendChild(badge);
            });
        } else {
            const msg = document.createElement("span");
            msg.style.cssText = "color: var(--text-muted); font-size: 0.85rem;";
            msg.textContent = "No primary keywords detected.";
            keywordsList.appendChild(msg);
        }
    }
});
