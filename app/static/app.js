document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const textInput = document.getElementById("news-text-input");
    const charCountEl = document.getElementById("char-count");
    const wordCountEl = document.getElementById("word-count");
    const btnPredict = document.getElementById("btn-predict");
    const btnClear = document.getElementById("btn-clear");
    
    const loaderSection = document.getElementById("loader-section");
    const resultSection = document.getElementById("result-section");
    
    // Result Detail Elements
    const verdictDisplay = document.getElementById("verdict-display");
    const verdictIcon = document.getElementById("verdict-icon");
    const verdictLabel = document.getElementById("verdict-label");
    const confidenceText = document.getElementById("confidence-percentage");
    const confidenceFill = document.getElementById("confidence-fill");
    
    const statLang = document.getElementById("stat-lang");
    const statWords = document.getElementById("stat-words");
    const statModel = document.getElementById("stat-model");
    const keywordsList = document.getElementById("keywords-list");



    // Preset Sample Data
    const presets = {
        "bm-fake": "Awas! Virus baru yang disebarkan melalui udara kini sedang melanda beberapa kawasan perumahan. Sila sebarkan maklumat ini dengan segera sebelum terlambat dan elakkan keluar rumah tanpa tujuan penting!",
        "bm-real": "Kementerian Kesihatan Malaysia (KKM) menasihatkan orang ramai supaya sentiasa mengambil langkah-langkah pencegahan penyakit berjangkit dengan memakai pelitup muka di kawasan sesak dan mengamalkan basuh tangan menggunakan sabun secara berkala.",
        "en-fake": "Amazing scientific secret! Drinking freshly squeezed lemon juice mixed with warm water every morning completely cures and protects you from all viral infections and flu. Share this post immediately with your friends and family to save lives!",
        "en-real": "Bank Negara Malaysia (BNM) announced that the Monetary Policy Committee has decided to maintain the Overnight Policy Rate (OPR) at 3.00 percent, citing stable domestic demand and moderate inflation levels in the national economy."
    };

    // Update character and word count in real-time
    function updateCounters() {
        const text = textInput.value;
        charCountEl.textContent = text.length;
        
        const trimmed = text.trim();
        const words = trimmed === "" ? 0 : trimmed.split(/\s+/).length;
        wordCountEl.textContent = words;
    }

    textInput.addEventListener("input", updateCounters);

    // Click Example Presets
    document.querySelectorAll(".preset-btn").forEach(button => {
        button.addEventListener("click", () => {
            const key = button.getAttribute("data-preset");
            if (presets[key]) {
                textInput.value = presets[key];
                updateCounters();
                
                // Visual click effect
                button.style.transform = "scale(0.96)";
                setTimeout(() => {
                    button.style.transform = "scale(1)";
                }, 150);
            }
        });
    });

    // Clear Button
    btnClear.addEventListener("click", () => {
        textInput.value = "";
        updateCounters();
        resultSection.classList.add("inactive");
        loaderSection.classList.add("hidden");
        textInput.focus();
    });

    // Predict/Verify Button Click
    btnPredict.addEventListener("click", async () => {
        const text = textInput.value.trim();
        const wordsCount = text === "" ? 0 : text.split(/\s+/).length;

        if (wordsCount < 3) {
            alert("Please enter a longer text block (at least 3 words) to analyze.");
            return;
        }

        // Show Loader, Hide Old Results
        resultSection.classList.add("inactive");
        loaderSection.classList.remove("hidden");
        btnPredict.disabled = true;

        try {
            const response = await fetch("/api/predict", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ text: text })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || "API classification request failed.");
            }

            const data = await response.json();
            displayResults(data);
        } catch (error) {
            alert(`Error: ${error.message}`);
            loaderSection.classList.add("hidden");
        } finally {
            btnPredict.disabled = false;
        }
    });

    // Display prediction outputs
    function displayResults(data) {
        // Hide Loader, Show Results Box
        loaderSection.classList.add("hidden");
        resultSection.classList.remove("inactive");

        // Format Verdict Class & Text
        const isFake = data.prediction === "Fake";
        
        // Update Verdict Classes
        verdictDisplay.className = "verdict-display " + (isFake ? "state-fake" : "state-real");
        resultSection.className = "card result-card " + (isFake ? "state-fake" : "state-real");

        // Set Text labels
        verdictLabel.textContent = isFake ? "SUSPECTED FAKE" : "CONFIRMED REAL";
        
        // Update Icon
        if (isFake) {
            verdictIcon.className = "fa-solid fa-triangle-exclamation";
        } else {
            verdictIcon.className = "fa-solid fa-circle-check";
        }

        // Update Confidence Gauge
        const confidenceVal = (data.confidence * 100).toFixed(1);
        confidenceText.textContent = `${confidenceVal}%`;
        confidenceFill.style.width = `${confidenceVal}%`;

        // Update Statistics Boxes
        statLang.textContent = data.language;
        statWords.textContent = data.word_count;
        statModel.textContent = "LogReg (93.99%)";

        // Populate keywords detected (vocab tokens)
        keywordsList.innerHTML = "";
        if (data.keywords_detected && data.keywords_detected.length > 0) {
            data.keywords_detected.forEach(word => {
                const badge = document.createElement("span");
                badge.className = "keyword-badge";
                badge.textContent = word;
                keywordsList.appendChild(badge);
            });
        } else {
            const emptyMsg = document.createElement("span");
            emptyMsg.style.color = "var(--text-secondary)";
            emptyMsg.style.fontSize = "0.9rem";
            emptyMsg.textContent = "No primary training vocabulary keywords detected.";
            keywordsList.appendChild(emptyMsg);
        }
    }
});
