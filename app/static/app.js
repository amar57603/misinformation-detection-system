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
    const themeSelector    = document.getElementById("theme-selector");
    const btnToggleAux     = document.getElementById("btn-toggle-aux");
    const auxPanel         = document.getElementById("aux-panel");
    const appLayout        = document.querySelector(".app-layout");

    // ── Theme & Mode Toggle ──────────────────────────────────────────
    const savedTheme = localStorage.getItem("siasatai_theme_name") || "default";
    const savedMode = localStorage.getItem("siasatai_theme_mode") || "dark";
    
    if (themeSelector) {
        themeSelector.value = savedTheme;
    }
    applyTheme(savedTheme, savedMode);

    function applyTheme(themeName, themeMode) {
        document.documentElement.setAttribute("data-theme", themeName);
        document.documentElement.setAttribute("data-mode", themeMode);
        
        if (themeMode === "light") {
            themeIcon.className = "fa-solid fa-moon";
        } else {
            themeIcon.className = "fa-solid fa-sun";
        }
        
        localStorage.setItem("siasatai_theme_name", themeName);
        localStorage.setItem("siasatai_theme_mode", themeMode);
    }

    if (themeSelector) {
        themeSelector.addEventListener("change", (e) => {
            const currentMode = localStorage.getItem("siasatai_theme_mode") || "dark";
            applyTheme(e.target.value, currentMode);
        });
    }

    btnThemeToggle.addEventListener("click", () => {
        const currentTheme = localStorage.getItem("siasatai_theme_name") || "default";
        const currentMode = localStorage.getItem("siasatai_theme_mode") || "dark";
        applyTheme(currentTheme, currentMode === "dark" ? "light" : "dark");
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
    let auxVisible = false;

    // ── Preset Texts ──────────────────────────────────────────
    const presets = {
        "bm-fake": "Awas penduduk Melaka! MBMB didedahkan sedang merancang untuk merobohkan seluruh kawasan Jonker Street dan mengusir peniaga lama secara paksa tanpa pampasan! Ribuan peniaga akan kehilangan punca rezeki mereka dalam masa dua minggu! Ini angkara projek rahsia yang melibatkan syarikat asing! Sebarkan segera untuk selamatkan warisan Melaka sebelum terlambat! Majlis Bandaraya Melaka Bersejarah tidak peduli nasib rakyat jelata!",
        "bm-real": "Majlis Bandaraya Melaka Bersejarah telah melancarkan aplikasi mudah alih rasmi yang membolehkan penduduk membuat aduan berkaitan perkhidmatan perbandaran, memohon lesen perniagaan, dan membayar bil cukai taksiran secara dalam talian tanpa perlu hadir ke pejabat. Lebih daripada sepuluh ribu pengguna telah mendaftar dalam tempoh dua minggu pertama sejak aplikasi dilancarkan oleh pihak berkuasa tempatan bagi meningkatkan kecekapan perkhidmatan awam kepada warga bandar.",
        "en-fake": "BREAKING: Scientists CONFIRM that 5G towers are secretly spreading a new airborne pathogen designed to control human DNA! Governments worldwide are covering up this shocking truth. Your immune system is being destroyed right now! Share this urgent warning immediately before it gets deleted. Drink bleach mixed with apple cider vinegar to detoxify your body from radiation poisoning. Big Pharma does not want you to know this secret cure that eliminates all diseases permanently.",
        "en-real": "The Department of Statistics Malaysia released its latest Consumer Price Index report showing that headline inflation rose by two point three percent year-on-year in the third quarter, driven primarily by higher food and beverage prices as well as increased transportation costs. The Statistics Department noted that core inflation, which excludes volatile food and fuel prices, remained relatively stable at one point eight percent, indicating that underlying demand pressures in the domestic economy are well-contained. Analysts expect the central bank to maintain its current monetary policy stance at the upcoming committee meeting given the moderate inflation outlook."
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
                <div class="history-preview"></div>
                <div class="history-meta">
                    <span><i class="fa-solid fa-language"></i> ${item.language}</span>
                    <span><i class="fa-solid fa-font"></i> ${item.word_count} words</span>
                    <span><i class="fa-regular fa-clock"></i> ${formatTime(item.timestamp)}</span>
                </div>
            `;
            el.querySelector(".history-preview").textContent = item.text.substring(0, 100) + (item.text.length > 100 ? "…" : "");
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

    function toggleAux(force) {
        auxVisible = (force !== undefined) ? force : !auxVisible;
        auxPanel.classList.toggle("hidden", !auxVisible);
        appLayout.classList.toggle("aux-active", auxVisible);
        const icon = btnToggleAux.querySelector("i");
        icon.className = auxVisible ? "fa-solid fa-xmark" : "fa-solid fa-chart-line";
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

    // Auxiliary toggle
    btnToggleAux.addEventListener("click", () => toggleAux());

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
        const text = `[SiasatAI by Amar Syakir Mazlan]\nVerdict: ${isFake ? "⚠ SUSPECTED FAKE" : "✓ CONFIRMED REAL"}\nConfidence: ${(lastResult.confidence * 100).toFixed(1)}%\nLanguage: ${lastResult.language}\n\nText: "${lastResult.text.substring(0, 200)}..."`;
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
                if (response.status === 429) {
                    const err = await response.json();
                    showToast(err.detail || "Too many requests. Please try again later.", "fa-triangle-exclamation");
                    throw new Error("rate_limit_exceeded");
                }
                const err = await response.json();
                throw new Error(err.detail || "API request failed.");
            }

            const data = await response.json();
            displayResults(data);
            addToHistory(data);

        } catch (error) {
            showState("idle");
            if (error.message !== "rate_limit_exceeded") {
                showToast(`Error: ${error.message}`, "fa-circle-xmark");
            }
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
        confidenceFill.style.width = "0%";
        setTimeout(() => { confidenceFill.style.width = `${pct}%`; }, 50);

        // Sensationalism & Tone Meter
        const tonePctEl   = document.getElementById("tone-percentage");
        const toneFillEl  = document.getElementById("tone-fill");
        const toneLabelEl = document.getElementById("tone-label");

        if (tonePctEl && toneFillEl && toneLabelEl) {
            const toneRaw = (data.sensationalism_score !== undefined ? data.sensationalism_score : 0) * 100;
            // Use a minimum display width of 3% so the bar is always visible
            const toneDisplay = Math.max(toneRaw, 3);

            tonePctEl.textContent = `${toneRaw.toFixed(1)}%`;
            toneFillEl.style.width = "0%";
            setTimeout(() => { toneFillEl.style.width = `${toneDisplay}%`; }, 50);

            if (toneRaw < 30) {
                toneLabelEl.textContent = `✓ Low Sensationalism — formal, objective writing style`;
                toneLabelEl.style.color = "var(--success)";
            } else if (toneRaw < 60) {
                toneLabelEl.textContent = `⚠ Moderate — contains some urgent or emotional phrasing`;
                toneLabelEl.style.color = "#fbbf24";
            } else {
                toneLabelEl.textContent = `✗ High — strong clickbait or rumor-style language detected`;
                toneLabelEl.style.color = "var(--danger)";
            }
        }

        statLang.textContent  = data.language;
        statWords.textContent = data.word_count;
        statModel.textContent = "LogReg (93.99%)";

        // Keywords
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

        // Word Cloud
        drawWordCloud(data.word_frequencies || [], isFake);

        // Summary
        const summaryEl = document.getElementById("summary-text");
        summaryEl.textContent = data.summary || "No summary available.";

        // Fact-check Sources
        const sourcesSection = document.getElementById("sources-section");
        const sourcesList    = document.getElementById("sources-list");
        sourcesList.innerHTML = "";
        if (data.fact_check_sources && data.fact_check_sources.length > 0) {
            sourcesSection.classList.remove("hidden");
            data.fact_check_sources.forEach(src => {
                const card = document.createElement("a");
                card.className = "source-card";
                card.href = src.url;
                card.target = "_blank";
                card.rel = "noopener noreferrer";
                card.innerHTML = `
                    <span class="source-flag">${src.flag}</span>
                    <div class="source-info">
                        <div class="source-name">${src.name} <i class="fa-solid fa-arrow-up-right-from-square"></i></div>
                        <div class="source-desc">${src.description}</div>
                    </div>`;
                sourcesList.appendChild(card);
            });
        } else {
            sourcesSection.classList.add("hidden");
        }
    }

    // ── Word Cloud (Canvas) ───────────────────────────────────
    function drawWordCloud(words, isFake) {
        const canvas = document.getElementById("wordcloud-canvas");
        const ctx    = canvas.getContext("2d");
        const W = canvas.offsetWidth  || 400;
        const H = canvas.offsetHeight || 160;
        canvas.width  = W;
        canvas.height = H;
        ctx.clearRect(0, 0, W, H);

        if (!words || words.length === 0) return;

        const isLight = document.documentElement.getAttribute("data-theme") === "light";
        const maxCount = words[0].count || 1;

        // Color palette
        const fakeColors  = ["#f87171","#fb923c","#fbbf24","#f472b6","#e879f9"];
        const realColors  = ["#34d399","#60a5fa","#818cf8","#38bdf8","#4ade80"];
        const lightFake   = ["#dc2626","#ea580c","#ca8a04","#db2777","#9333ea"];
        const lightReal   = ["#059669","#2563eb","#4f46e5","#0284c7","#16a34a"];
        const palette = isLight
            ? (isFake ? lightFake : lightReal)
            : (isFake ? fakeColors : realColors);

        const placed = [];

        words.slice(0, 30).forEach(({ word, count }) => {
            const ratio    = count / maxCount;
            const fontSize = Math.max(11, Math.min(36, Math.round(12 + ratio * 26)));
            ctx.font       = `${600 + (ratio > 0.5 ? 200 : 0)} ${fontSize}px Outfit, sans-serif`;
            const textW    = ctx.measureText(word).width;
            const color    = palette[Math.floor(Math.random() * palette.length)];
            ctx.fillStyle  = color;

            // Try to place word without overlap
            let placed_ = false;
            for (let attempt = 0; attempt < 60; attempt++) {
                const x = Math.random() * (W - textW - 10) + 5;
                const y = Math.random() * (H - fontSize - 4) + fontSize;
                const box = { x, y: y - fontSize, w: textW, h: fontSize + 4 };
                const overlap = placed.some(p =>
                    x < p.x + p.w && x + textW > p.x &&
                    box.y < p.y + p.h && box.y + box.h > p.y
                );
                if (!overlap) {
                    ctx.globalAlpha = 0.6 + ratio * 0.4;
                    ctx.fillText(word, x, y);
                    placed.push(box);
                    placed_ = true;
                    break;
                }
            }
            ctx.globalAlpha = 1;
        });
    }

    // ── Accordion Toggles ─────────────────────────────────────
    document.querySelectorAll(".accordion-header").forEach(header => {
        header.addEventListener("click", () => {
            const item = header.parentElement;
            const body = item.querySelector(".accordion-body");
            const isActive = item.classList.contains("active");

            // Close all items
            document.querySelectorAll(".accordion-item").forEach(i => {
                i.classList.remove("active");
                i.querySelector(".accordion-body").style.maxHeight = null;
            });

            // Toggle active state
            if (!isActive) {
                item.classList.add("active");
                body.style.maxHeight = body.scrollHeight + "px";
            }
        });
    });

    // ── Feedback Form Handler ──────────────────────────────────
    const feedbackForm  = document.getElementById("aux-feedback-form");
    const successState  = document.getElementById("feedback-success-state");
    const btnResetFeed  = document.getElementById("btn-reset-feedback");

    if (feedbackForm) {
        feedbackForm.addEventListener("submit", async (e) => {
            e.preventDefault();

            const categoryEl = document.getElementById("feedback-category");
            const notesEl = document.getElementById("feedback-notes");
            const submitBtn = feedbackForm.querySelector(".btn-submit-feedback");

            if (!categoryEl || !notesEl) return;

            const category = categoryEl.value;
            const notes = notesEl.value;

            // Prepare Web3Forms payload
            const payload = {
                // Public Web3Forms form token (safe to expose client-side)
                access_key: "5e5fae3d-9e5a-41e6-bcfa-b5e9f6378030",
                subject: `SiasatAI Feedback: [${category.toUpperCase()}]`,
                from_name: "SiasatAI App",
                category: category,
                notes: notes,
                timestamp: new Date().toISOString()
            };

            // Include last result details if available to give context
            if (lastResult) {
                payload.article_text = lastResult.text || textInput.value;
                payload.prediction = lastResult.prediction || "N/A";
                payload.confidence = lastResult.confidence ? `${(lastResult.confidence * 100).toFixed(1)}%` : "N/A";
                payload.language = lastResult.language || "N/A";
                payload.word_count = lastResult.word_count || "N/A";
            } else {
                payload.article_text = textInput.value || "No article text analyzed";
                payload.prediction = "N/A (No prediction run)";
                payload.confidence = "N/A";
                payload.language = "N/A";
                payload.word_count = "N/A";
            }

            // Disable button and show spinner
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Sending...';
            }

            try {
                const response = await fetch("https://api.web3forms.com/submit", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    body: JSON.stringify(payload)
                });

                const result = await response.json();

                if (response.ok && result.success) {
                    feedbackForm.classList.add("hidden");
                    successState.classList.remove("hidden");
                    showToast("Feedback submitted successfully!", "fa-circle-check");
                } else {
                    throw new Error(result.message || "Failed to submit feedback.");
                }
            } catch (error) {
                showToast(`Error: ${error.message}`, "fa-circle-xmark");
            } finally {
                if (submitBtn) {
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fa-solid fa-paper-plane"></i> Send Feedback';
                }
            }
        });
    }

    if (btnResetFeed) {
        btnResetFeed.addEventListener("click", () => {
            feedbackForm.reset();
            successState.classList.add("hidden");
            feedbackForm.classList.remove("hidden");
        });
    }

    // ── Load Global Model Diagnostics ───────────────────────
    async function loadModelDiagnostics() {
        const fakeChart = document.getElementById("fake-signals-chart");
        const realChart = document.getElementById("real-signals-chart");

        try {
            const response = await fetch("/api/model_info");
            if (!response.ok) throw new Error("Could not load model diagnostics.");

            const data = await response.json();

            // Populate fake signals chart
            if (fakeChart && data.top_fake_features) {
                fakeChart.innerHTML = "";
                const maxWeight = Math.max(...data.top_fake_features.map(f => Math.abs(f.weight)), 0.1);

                data.top_fake_features.forEach(feat => {
                    const absWeight = Math.abs(feat.weight);
                    const percent = (absWeight / maxWeight) * 100;
                    const row = document.createElement("div");
                    row.className = "signal-bar-row";
                    row.innerHTML = `
                        <div class="signal-word" title="${feat.word}">${feat.word}</div>
                        <div class="signal-bar-wrapper">
                            <div class="signal-bar-fill fake" style="width: 0%;"></div>
                        </div>
                        <div class="signal-weight-label">${feat.weight.toFixed(2)}</div>
                    `;
                    fakeChart.appendChild(row);
                    setTimeout(() => {
                        row.querySelector(".signal-bar-fill").style.width = `${percent}%`;
                    }, 100);
                });
            }

            // Populate real signals chart
            if (realChart && data.top_real_features) {
                realChart.innerHTML = "";
                const maxWeight = Math.max(...data.top_real_features.map(f => f.weight), 0.1);

                data.top_real_features.forEach(feat => {
                    const percent = (feat.weight / maxWeight) * 100;
                    const row = document.createElement("div");
                    row.className = "signal-bar-row";
                    row.innerHTML = `
                        <div class="signal-word" title="${feat.word}">${feat.word}</div>
                        <div class="signal-bar-wrapper">
                            <div class="signal-bar-fill real" style="width: 0%;"></div>
                        </div>
                        <div class="signal-weight-label">+${feat.weight.toFixed(2)}</div>
                    `;
                    realChart.appendChild(row);
                    setTimeout(() => {
                        row.querySelector(".signal-bar-fill").style.width = `${percent}%`;
                    }, 100);
                });
            }

        } catch (error) {
            console.error("Error loading model diagnostics:", error);
            if (fakeChart) fakeChart.innerHTML = '<div class="signals-loading" style="color: var(--danger);"><i class="fa-solid fa-circle-exclamation"></i> Load failed.</div>';
            if (realChart) realChart.innerHTML = '<div class="signals-loading" style="color: var(--danger);"><i class="fa-solid fa-circle-exclamation"></i> Load failed.</div>';
        }
    }

    // Load on start
    loadModelDiagnostics();
});
