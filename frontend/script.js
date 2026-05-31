// ==========================================
// CONFIGURATION & CONSTANTS
// ==========================================
const BACKEND_URL = "http://127.0.0.1:5000";

// ==========================================
// LOCAL STATE MANAGEMENT
// ==========================================
let activeMode = "general"; // general, guidance, resume, placement
let targetRole = "Web Developer";
let sessionId = "session_" + Math.random().toString(36).substr(2, 9);
let selectedFile = null;

// Mode definitions for visuals
const MODE_METADATA = {
    general: {
        title: "General Chat",
        subtitle: "Ask questions about career fields or placement preparation.",
        avatar: "🤖",
        chips: ["What is this bot for?", "Tell me about the tech roles", "Explain the ML architecture"]
    },
    guidance: {
        title: "Career Guidance",
        subtitle: "Describe your skills & interests. Let ML predict your path.",
        avatar: "🧭",
        chips: ["Predict my career role", "What makes a strong portfolio?", "Which technologies are in demand?"]
    },
    resume: {
        title: "Resume Analyzer",
        subtitle: "Submit your resume to check your ATS compatibility score.",
        avatar: "📄",
        chips: ["How is the ATS score calculated?", "List recommended keywords", "Why are skills missing?"]
    },
    placement: {
        title: "Placement Prep",
        subtitle: "Solve mock questions and study expert tech preparation tips.",
        avatar: "💼",
        chips: ["Give me a mock question", "Give me coding tips", "Give me communication advice"]
    }
};

// ==========================================
// DOM ELEMENT QUERIES
// ==========================================
document.addEventListener("DOMContentLoaded", () => {
    // Mode Buttons
    const btnGeneral = document.getElementById("btn-mode-general");
    const btnGuidance = document.getElementById("btn-mode-guidance");
    const btnResume = document.getElementById("btn-mode-resume");
    const btnPlacement = document.getElementById("btn-mode-placement");
    const modeButtons = [btnGeneral, btnGuidance, btnResume, btnPlacement];

    // Settings & Navigation
    const selectTargetRole = document.getElementById("select-target-role");
    const themeToggleBtn = document.getElementById("theme-toggle");
    const serverStatusText = document.getElementById("server-status");
    const serverStatusDot = document.querySelector(".status-dot");
    const chatTitle = document.getElementById("chat-title");
    const chatSubtitle = document.getElementById("chat-subtitle");
    const modeAvatar = document.getElementById("mode-avatar");
    const btnClearChat = document.getElementById("btn-clear-chat");

    // Chat Containers
    const chatMessages = document.getElementById("chat-messages");
    const chatInput = document.getElementById("chat-input");
    const btnSendMessage = document.getElementById("btn-send-message");
    const quickChipsContainer = document.getElementById("quick-chips");

    // Insights Cards
    const cardDefault = document.getElementById("card-default-insights");
    const cardML = document.getElementById("card-ml-insights");
    const cardResume = document.getElementById("card-resume-insights");
    const cardPlacement = document.getElementById("card-placement-insights");
    const insightsCards = [cardDefault, cardML, cardResume, cardPlacement];

    // ML Predictor Panel Elements
    const skillsInput = document.getElementById("skills-input");
    const interestsInput = document.getElementById("interests-input");
    const btnPredictRole = document.getElementById("btn-predict-role");
    const predictionResultsContainer = document.getElementById("prediction-results-container");
    const mlChart = document.getElementById("ml-chart");

    // Resume Analyzer Panel Elements
    const tabUploadBtn = document.querySelector('[data-tab="tab-upload"]');
    const tabPasteBtn = document.querySelector('[data-tab="tab-paste"]');
    const tabUploadContent = document.getElementById("tab-upload");
    const tabPasteContent = document.getElementById("tab-paste");
    const dropZone = document.getElementById("drop-zone-resume");
    const fileInput = document.getElementById("file-resume");
    const fileInfoContainer = document.getElementById("file-info-container");
    const selectedFileName = document.getElementById("selected-file-name");
    const btnClearFile = document.getElementById("btn-clear-file");
    const pasteResumeText = document.getElementById("paste-resume-text");
    const btnAnalyzeResume = document.getElementById("btn-analyze-resume");
    const atsResultsContainer = document.getElementById("ats-results-container");
    const atsScoreNum = document.getElementById("ats-score-num");
    const scoreProgressCircle = document.getElementById("score-progress");
    const matchingSkillsList = document.getElementById("matching-skills-list");
    const missingSkillsList = document.getElementById("missing-skills-list");

    // Placement Panel Control buttons
    const placementControlBtns = document.querySelectorAll(".control-btn");
    const prepRoleLabel = document.getElementById("prep-role-label");

    // ==========================================
    // BACKEND CONNECTION HEALTHCHECK
    // ==========================================
    async function checkBackendStatus() {
        try {
            const response = await fetch(`${BACKEND_URL}/api/status`);
            if (response.ok) {
                const data = await response.json();
                serverStatusText.textContent = "Backend: Online";
                serverStatusDot.className = "status-dot green pulsing";
                console.log("Connected to Flask backend successfully. Available roles:", data.available_roles);
            } else {
                throw new Error();
            }
        } catch (error) {
            serverStatusText.textContent = "Backend: Offline (Port 5000)";
            serverStatusDot.className = "status-dot pulsing";
            serverStatusDot.style.background = "#ef4444";
            console.warn("Could not connect to Flask backend. Please start app.py first.");
        }
    }
    
    checkBackendStatus();
    // Recheck status every 10 seconds
    setInterval(checkBackendStatus, 10000);

    // ==========================================
    // THEME HANDLING
    // ==========================================
    // Check saved theme or system preference
    const savedTheme = localStorage.getItem("theme") || "dark";
    if (savedTheme === "light") {
        document.body.className = "light-theme";
        themeToggleBtn.querySelector(".toggle-icon").textContent = "🌙";
    }

    themeToggleBtn.addEventListener("click", () => {
        if (document.body.classList.contains("dark-theme")) {
            document.body.className = "light-theme";
            themeToggleBtn.querySelector(".toggle-icon").textContent = "🌙";
            localStorage.setItem("theme", "light");
        } else {
            document.body.className = "dark-theme";
            themeToggleBtn.querySelector(".toggle-icon").textContent = "☀️";
            localStorage.setItem("theme", "dark");
        }
    });

    // ==========================================
    // MODE SWITCHER LOGIC
    // ==========================================
    function switchMode(mode) {
        activeMode = mode;
        const meta = MODE_METADATA[mode];

        // Update navigation states
        modeButtons.forEach(btn => {
            if (btn.getAttribute("data-mode") === mode) {
                btn.classList.add("active");
            } else {
                btn.classList.remove("active");
            }
        });

        // Update Chat Header
        chatTitle.textContent = meta.title;
        chatSubtitle.textContent = meta.subtitle;
        modeAvatar.textContent = meta.avatar;

        // Show relevant Insights Card on the right
        insightsCards.forEach(card => card.classList.add("hidden"));
        if (mode === "general") cardDefault.classList.remove("hidden");
        if (mode === "guidance") cardML.classList.remove("hidden");
        if (mode === "resume") cardResume.classList.remove("hidden");
        if (mode === "placement") {
            cardPlacement.classList.remove("hidden");
            prepRoleLabel.textContent = targetRole;
        }

        // Render mode-specific Quick Chips
        quickChipsContainer.innerHTML = "";
        meta.chips.forEach(chipText => {
            const btn = document.createElement("button");
            btn.className = "chip";
            btn.textContent = chipText;
            btn.setAttribute("data-text", chipText);
            btn.addEventListener("click", () => handleSendMessage(chipText));
            quickChipsContainer.appendChild(btn);
        });

        // Clean input focus
        chatInput.focus();
    }

    // Assign click listeners to nav buttons
    modeButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            switchMode(btn.getAttribute("data-mode"));
        });
    });

    // Update target role from settings dropdown
    selectTargetRole.addEventListener("change", (e) => {
        targetRole = e.target.value;
        prepRoleLabel.textContent = targetRole;
        console.log(`Target role updated to: ${targetRole}`);
    });

    // ==========================================
    // CHAT MESSAGE RENDERING & PROCESSING
    // ==========================================
    // Format response text with rich bold tags and interactive spoilers
    function formatMessageText(text) {
        // Step 1: Extract spoilers BEFORE escaping so we can match **Explanation:** correctly
        const spoilerRegex = /\|\|([\s\S]*?)\|\|/g;
        const spoilerPlaceholders = [];
        let processedText = text.replace(spoilerRegex, (match, content) => {
            let header = "Click to Reveal Answer";
            let desc = content.trim();

            // Match both **Explanation:** and plain Explanation:
            if (desc.startsWith("**Explanation:**")) {
                header = "View Explanation";
                desc = desc.replace("**Explanation:**", "").trim();
            } else if (desc.startsWith("Explanation:")) {
                header = "View Explanation";
                desc = desc.replace("Explanation:", "").trim();
            }

            // Apply bold formatting inside the explanation text too
            desc = desc.replace(/\*\*([\s\S]*?)\*\*/g, "<strong>$1</strong>");

            const placeholder = `%%SPOILER_${spoilerPlaceholders.length}%%`;
            spoilerPlaceholders.push(`
                <div class="spoiler-container">
                    <div class="spoiler-header" onclick="this.nextElementSibling.classList.toggle('revealed'); this.textContent = this.nextElementSibling.classList.contains('revealed') ? 'Hide Explanation ▲' : 'View Explanation ▼'">
                        ${header} <span>▼</span>
                    </div>
                    <div class="spoiler-content">${desc}</div>
                </div>
            `);
            return placeholder;
        });

        // Step 2: Escape HTML special chars in non-spoiler text
        let formatted = processedText
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Step 3: Convert **bold** to <strong>
        formatted = formatted.replace(/\*\*([\s\S]*?)\*\*/g, "<strong>$1</strong>");

        // Step 4: Convert * bullet points to <li>
        formatted = formatted.replace(/^\s*\*\s+(.*)$/gm, "<li>$1</li>");
        formatted = formatted.replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>");

        // Step 5: Convert newlines to <br>
        formatted = formatted.replace(/\n/g, "<br>");

        // Step 6: Restore spoiler HTML (unescape the placeholder tags)
        spoilerPlaceholders.forEach((html, i) => {
            formatted = formatted.replace(`%%SPOILER_${i}%%`, html);
        });

        return formatted;
    }

    function addMessage(sender, text) {
        const messageDiv = document.createElement("div");
        messageDiv.className = `message ${sender}-message`;

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = sender === "user" ? "👨‍🎓" : MODE_METADATA[activeMode].avatar;

        const content = document.createElement("div");
        content.className = "message-content";
        content.innerHTML = formatMessageText(text);

        messageDiv.appendChild(avatar);
        messageDiv.appendChild(content);
        chatMessages.appendChild(messageDiv);
        
        // Instant scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Add pulsing typing animation
    function showTypingIndicator() {
        const typingDiv = document.createElement("div");
        typingDiv.className = "message bot-message typing-indicator-container";
        typingDiv.id = "typing-indicator";

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = MODE_METADATA[activeMode].avatar;

        const content = document.createElement("div");
        content.className = "message-content typing-indicator";
        content.innerHTML = `
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
        `;

        typingDiv.appendChild(avatar);
        typingDiv.appendChild(content);
        chatMessages.appendChild(typingDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = document.getElementById("typing-indicator");
        if (indicator) {
            indicator.remove();
        }
    }

    async function handleSendMessage(customText = null) {
        const text = (customText || chatInput.value).trim();
        if (!text) return;

        // Reset chat input field
        if (!customText) chatInput.value = "";
        
        // Adjust textbox size
        chatInput.style.height = "auto";

        // Render user bubble
        addMessage("user", text);

        // Show typing indicator
        showTypingIndicator();

        try {
            const response = await fetch(`${BACKEND_URL}/api/chat`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    message: text,
                    mode: activeMode,
                    session_id: sessionId,
                    target_role: targetRole
                })
            });

            removeTypingIndicator();

            if (response.ok) {
                const data = await response.json();
                addMessage("bot", data.response);
                
                // If backend processed role predictions, update the ML panel automatically!
                if (data.extra && data.extra.predictions) {
                    renderMLChart(data.extra.predictions);
                }
            } else {
                throw new Error();
            }
        } catch (e) {
            removeTypingIndicator();
            addMessage("bot", "⚠️ **Connection Error:** I was unable to connect to the Flask server. Please make sure `app.py` is running on `http://127.0.0.1:5000`.");
        }
    }

    // Bind sendMessage listeners
    btnSendMessage.addEventListener("click", () => handleSendMessage());
    
    chatInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Auto-expand textarea on typing
    chatInput.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight - 10) + "px";
    });

    // Clear Chat Handler
    btnClearChat.addEventListener("click", async () => {
        try {
            await fetch(`${BACKEND_URL}/api/chat/${sessionId}`, { method: "DELETE" });
            chatMessages.innerHTML = `
                <div class="message bot-message">
                    <div class="message-avatar">🤖</div>
                    <div class="message-content">
                        <p>Chat history cleared successfully for session!</p>
                    </div>
                </div>
            `;
        } catch (e) {
            chatMessages.innerHTML = "";
            addMessage("bot", "Local chat UI cleared.");
        }
    });

    // Quick chips initial actions
    quickChipsContainer.querySelectorAll(".chip").forEach(btn => {
        btn.addEventListener("click", () => {
            handleSendMessage(btn.getAttribute("data-text"));
        });
    });

    // ==========================================
    // ML PREDICTION LOGIC (INSIGHTS)
    // ==========================================
    function renderMLChart(predictions) {
        predictionResultsContainer.classList.remove("hidden");
        mlChart.innerHTML = "";

        predictions.forEach(p => {
            const row = document.createElement("div");
            row.className = "chart-row";
            
            row.innerHTML = `
                <div class="chart-labels">
                    <span>${p.role}</span>
                    <span>${p.confidence}%</span>
                </div>
                <div class="chart-bar-bg">
                    <div class="chart-bar-fill" style="width: 0%;"></div>
                </div>
            `;
            
            mlChart.appendChild(row);
            
            // Trigger animation on bar fill
            setTimeout(() => {
                row.querySelector(".chart-bar-fill").style.width = `${p.confidence}%`;
            }, 100);
        });
    }

    btnPredictRole.addEventListener("click", async () => {
        const skills = skillsInput.value.trim();
        const interests = interestsInput.value.trim();

        if (!skills && !interests) {
            alert("Please fill in either your skills or interests!");
            return;
        }

        btnPredictRole.textContent = "Analyzing skills... ⏳";
        btnPredictRole.disabled = true;

        try {
            const response = await fetch(`${BACKEND_URL}/api/predict-role`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ skills, interests })
            });

            if (response.ok) {
                const data = await response.json();
                renderMLChart(data.predictions);

                // Formulate a beautiful summary to put into the chat too!
                let chatSummary = `🤖 **ML Prediction Complete!**\n\nI processed your skills & interests. My Scikit-Learn classification model predicted **${data.recommended_role}** as your optimal career role.\n\n### Recommended Career Roadmap:\n`;
                data.roadmap.forEach((step, idx) => {
                    chatSummary += `${idx+1}. ${step}\n`;
                });
                
                addMessage("bot", chatSummary);
            } else {
                throw new Error();
            }
        } catch (e) {
            alert("Prediction failed. Make sure the Flask backend is online!");
        } finally {
            btnPredictRole.textContent = "Run ML Predictor ⚡";
            btnPredictRole.disabled = false;
        }
    });

    // ==========================================
    // RESUME ANALYZER (INSIGHTS)
    // ==========================================
    // TAB NAVIGATION
    tabUploadBtn.addEventListener("click", () => {
        tabUploadBtn.classList.add("active");
        tabPasteBtn.classList.remove("active");
        tabUploadContent.classList.add("active");
        tabPasteContent.classList.remove("active");
    });

    tabPasteBtn.addEventListener("click", () => {
        tabPasteBtn.classList.add("active");
        tabUploadBtn.classList.remove("active");
        tabPasteContent.classList.add("active");
        tabUploadContent.classList.remove("active");
    });

    // FILE DRAG & DROP
    dropZone.addEventListener("click", () => fileInput.click());

    dropZone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropZone.classList.add("dragover");
    });

    dropZone.addEventListener("dragleave", () => {
        dropZone.classList.remove("dragover");
    });

    dropZone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropZone.classList.remove("dragover");
        if (e.dataTransfer.files.length > 0) {
            handleSelectedFile(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleSelectedFile(e.target.files[0]);
        }
    });

    function handleSelectedFile(file) {
        selectedFile = file;
        selectedFileName.textContent = file.name;
        fileInfoContainer.classList.remove("hidden");
        dropZone.classList.add("hidden");
    }

    btnClearFile.addEventListener("click", (e) => {
        e.stopPropagation();
        selectedFile = null;
        fileInput.value = "";
        fileInfoContainer.classList.add("hidden");
        dropZone.classList.remove("hidden");
    });

    // ANALYSIS INFERENCE
    btnAnalyzeResume.addEventListener("click", async () => {
        const formData = new FormData();
        formData.append("target_role", targetRole);

        const isUploadTab = tabUploadContent.classList.contains("active");
        
        if (isUploadTab) {
            if (!selectedFile) {
                alert("Please select or drop a resume PDF/TXT file first!");
                return;
            }
            formData.append("resume_file", selectedFile);
        } else {
            const pasteText = pasteResumeText.value.trim();
            if (!pasteText) {
                alert("Please paste your resume text first!");
                return;
            }
            formData.append("resume_text", pasteText);
        }

        btnAnalyzeResume.textContent = "Parsing Resume NLTK... ⏳";
        btnAnalyzeResume.disabled = true;

        try {
            const response = await fetch(`${BACKEND_URL}/api/analyze-resume`, {
                method: "POST",
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                
                // Show dashboard results container
                atsResultsContainer.classList.remove("hidden");
                
                // 1. Update score radial dial progress
                atsScoreNum.textContent = data.ats_score;
                const strokeOffset = 283 - (283 * data.ats_score) / 100;
                scoreProgressCircle.style.strokeDashoffset = strokeOffset;
                
                // Colors depending on score severity
                if (data.ats_score >= 70) {
                    scoreProgressCircle.style.stroke = "#10b981"; // green
                } else if (data.ats_score >= 45) {
                    scoreProgressCircle.style.stroke = "#f59e0b"; // yellow
                } else {
                    scoreProgressCircle.style.stroke = "#f43f5e"; // red
                }

                // 2. Populate Matched Skills
                matchingSkillsList.innerHTML = "";
                if (data.matching_skills.length === 0) {
                    matchingSkillsList.innerHTML = "<li>None found</li>";
                } else {
                    data.matching_skills.forEach(s => {
                        const li = document.createElement("li");
                        li.textContent = s;
                        matchingSkillsList.appendChild(li);
                    });
                }

                // 3. Populate Missing Skills
                missingSkillsList.innerHTML = "";
                if (data.missing_skills.length === 0) {
                    missingSkillsList.innerHTML = "<li>Perfect Match! ✓</li>";
                } else {
                    data.missing_skills.forEach(s => {
                        const li = document.createElement("li");
                        li.textContent = s;
                        missingSkillsList.appendChild(li);
                    });
                }

                // Send summary message directly into chat log!
                let chatMessage = `📄 **NLTK Resume Analysis Completed!**\n\n**Target Role:** ${targetRole}\n**ATS Compatibility Score:** **${data.ats_score}%**\n\n* **Extracted Skills:** ${data.extracted_skills.join(", ") || "None"}\n* **Matched Skills:** ${data.matching_skills.join(", ") || "None"}\n* **Critical Missing Skills:** ${data.missing_skills.join(", ") || "None"}\n\n### Career Advancement Roadmap:\n`;
                data.roadmap.forEach((step, idx) => {
                    chatMessage += `${idx+1}. ${step}\n`;
                });
                
                addMessage("bot", chatMessage);

            } else {
                const errData = await response.json();
                alert(`Error parsing resume: ${errData.error || "Server issue."}`);
            }
        } catch (e) {
            alert("Analysis failed. Make sure the Flask server is online!");
        } finally {
            btnAnalyzeResume.textContent = "Analyze Resume 🔍";
            btnAnalyzeResume.disabled = false;
        }
    });

    // ==========================================
    // PLACEMENT ASSISTANT QUICK TRIGGER BUTTONS
    // ==========================================
    placementControlBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            const triggerType = btn.getAttribute("data-type");
            let promptText = "";
            
            if (triggerType === "question") promptText = "Give me a mock interview question";
            if (triggerType === "coding") promptText = "Give me coding prep tips";
            if (triggerType === "aptitude") promptText = "Give me aptitude guidance";
            if (triggerType === "communication") promptText = "Give me communication soft skills advice";
            
            handleSendMessage(promptText);
        });
    });
});
