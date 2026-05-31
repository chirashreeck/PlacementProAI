import os
import time
from flask import Flask, request, jsonify
from flask_cors import CORS
from pypdf import PdfReader

# Import local ML and NLP modules
from backend.ml_engine import MLEngine
from backend.nlp_parser import NLPParser, ROLE_PROFILES

app = Flask(__name__)
# Enable CORS for all routes to prevent cross-origin issues during local front-end testing
CORS(app)

# Initialize engines
ml_engine = MLEngine()
nlp_parser = NLPParser()

# Simple in-memory session store for chat memory
sessions = {}

# High-quality Interview Preparation pool for roles
PLACEMENT_PREP_POOL = {
    "Web Developer": {
        "questions": [
            {"q": "Explain event delegation in JavaScript and why it is useful.", "a": "Event delegation is a technique where you attach a single event listener to a parent element rather than attaching multiple event listeners to individual child nodes. It leverages 'event bubbling'—events triggered on child nodes rise up to their parent. Benefits: uses less memory, simplifies dynamic content updates."},
            {"q": "What is the difference between CSS Flexbox and Grid?", "a": "Flexbox is designed for one-dimensional layouts—either a row OR a column. Grid is designed for two-dimensional layouts—both rows AND columns simultaneously. Use Flexbox for component alignment (like navbars) and Grid for entire page layout structures."},
            {"q": "What is the DOM and how does React optimize rendering?", "a": "The Document Object Model (DOM) is an XML/HTML document structured as a tree where each node is an object. Updating the real DOM is slow. React optimizes this by creating a lightweight 'Virtual DOM' in memory, comparing changes (Diffing Algorithm), and updating only the specific changed nodes in the real DOM (Reconciliation)."}
        ],
        "coding_tips": "Practice coding basic DOM manipulation and array methods (map, filter, reduce). Solve Easy/Medium strings and arrays tasks on LeetCode/HackerRank in JS.",
        "aptitude_tips": "Review simple numerical patterns, logical reasoning, and basic permutations/combinations.",
        "communication_advice": "Focus on explaining your thinking process aloud during live coding. Use the STAR method (Situation, Task, Action, Result) for behavioral questions."
    },
    "Data Analyst": {
        "questions": [
            {"q": "Explain the difference between a LEFT JOIN, RIGHT JOIN, and INNER JOIN in SQL.", "a": "INNER JOIN returns records that have matching values in both tables. LEFT JOIN returns all records from the left table, and matched records from the right; if no match, it fills with NULL. RIGHT JOIN does the reverse, returning all records from the right and matching from the left."},
            {"q": "What is overfitting in statistics and how do you avoid it?", "a": "Overfitting happens when a model fits the training data too closely, capturing noise instead of the underlying trend, leading to poor performance on unseen data. Avoid it by using cross-validation, simplifying the model features, adding regularization, or gathering more training data."},
            {"q": "Difference between Pandas Series and DataFrame?", "a": "A Series is a one-dimensional array-like object capable of holding any data type, similar to a single column in a spreadsheet. A DataFrame is a two-dimensional, size-mutable, tabular data structure with labeled axes (rows and columns), resembling a full spreadsheet table."}
        ],
        "coding_tips": "Practice complex SQL aggregates (GROUP BY, HAVING), window functions, joins, and Pandas data transformations.",
        "aptitude_tips": "Focus on data interpretation (interpreting bar/pie charts), statistics, probability, and percentages.",
        "communication_advice": "Practice translating complex data findings into actionable business terms. Focus on being structured and using visual charts to explain data."
    },
    "AI Engineer": {
        "questions": [
            {"q": "Explain the difference between supervised and unsupervised machine learning.", "a": "Supervised learning uses labeled training data—each input has a corresponding correct output (e.g. classification, regression). Unsupervised learning works on unlabeled data to discover hidden patterns or groupings (e.g., clustering with K-Means, dimensionality reduction with PCA)."},
            {"q": "What is gradient descent and how does it work?", "a": "Gradient descent is an optimization algorithm used to minimize a model's loss function. It iteratively calculates the gradient (derivative) of the loss function with respect to model parameters, and updates parameters in the opposite direction of the gradient to find the local minimum."},
            {"q": "Explain the concept of attention and self-attention in deep learning.", "a": "Attention allows a neural network to focus on specific parts of an input sequence when generating an output, rather than treating all parts equally. Self-attention (used in Transformers) relates different positions of a single sequence to compute a representation of the sequence, helping models capture long-range dependencies."}
        ],
        "coding_tips": "Implement basic neural networks or ML algorithms from scratch using Numpy. Understand PyTorch Tensor transformations and Scikit-Learn pipelines.",
        "aptitude_tips": "Review linear algebra (matrix multiplications, eigenvectors), calculus (derivatives, gradients), and probability distributions.",
        "communication_advice": "Explain technical design choices explicitly. Discuss trade-offs (e.g. inference time vs accuracy, model size vs deployment constraints) clearly."
    },
    "Cybersecurity Analyst": {
        "questions": [
            {"q": "What is the difference between symmetric and asymmetric cryptography?", "a": "Symmetric cryptography uses the same secret key for both encryption and decryption (e.g., AES), which is fast but has key distribution issues. Asymmetric cryptography uses a public key to encrypt and a separate private key to decrypt (e.g., RSA), which is secure for key exchange but slower."},
            {"q": "Explain the three-way handshake in TCP.", "a": "The TCP three-way handshake establishes a reliable connection: 1. The client sends a SYN (Synchronize) packet to the server. 2. The server responds with a SYN-ACK packet. 3. The client replies with an ACK (Acknowledge) packet, establishing the active session."},
            {"q": "What is an SQL Injection (SQLi) attack and how do you prevent it?", "a": "An SQL Injection is a vulnerability where an attacker injects malicious SQL statements into input fields to bypass security and access/modify database records. Prevention: Use parameterized queries/prepared statements, validate input, and employ stored procedures."}
        ],
        "coding_tips": "Master Linux bash command-line tools, port scanning concepts, and basic Python security scripts (socket programming, keyloggers).",
        "aptitude_tips": "Review binary systems, subnetting calculations, and logical gates (AND, OR, XOR).",
        "communication_advice": "Focus on calmness and precision. Explain security risks clearly to non-technical stakeholders and frame solutions in terms of risk mitigation."
    }
}

@app.route("/api/status", methods=["GET"])
def get_status():
    return jsonify({
        "status": "online",
        "ml_model_trained": ml_engine.trained,
        "available_roles": list(ROLE_PROFILES.keys())
    })

@app.route("/api/predict-role", methods=["POST"])
def api_predict_role():
    data = request.get_json() or {}
    skills = data.get("skills", "")
    interests = data.get("interests", "")
    
    if not skills and not interests:
        return jsonify({"error": "Please provide your skills or interests."}), 400
        
    combined_input = f"{skills} {interests}"
    predictions = ml_engine.predict_role(combined_input)
    
    # Take the top role and suggest a roadmap
    top_role = predictions[0]["role"]
    roadmap = ROLE_PROFILES.get(top_role, {}).get("roadmap", [])
    
    return jsonify({
        "predictions": predictions,
        "recommended_role": top_role,
        "roadmap": roadmap
    })

@app.route("/api/analyze-resume", methods=["POST"])
def api_analyze_resume():
    target_role = request.form.get("target_role", "Web Developer")
    resume_text = request.form.get("resume_text", "")
    
    # Check if a file was uploaded
    if "resume_file" in request.files:
        file = request.files["resume_file"]
        if file.filename != "":
            file_ext = os.path.splitext(file.filename)[1].lower()
            try:
                if file_ext == ".pdf":
                    # Extract text from PDF
                    pdf_reader = PdfReader(file)
                    extracted_text = []
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            extracted_text.append(page_text)
                    resume_text = "\n".join(extracted_text)
                elif file_ext in [".txt", ".md"]:
                    # Read text file
                    resume_text = file.read().decode("utf-8", errors="ignore")
                else:
                    return jsonify({"error": f"Unsupported file format '{file_ext}'. Please upload a PDF or TXT file."}), 400
            except Exception as e:
                return jsonify({"error": f"Failed to parse file: {str(e)}"}), 500
                
    if not resume_text or len(resume_text.strip()) < 10:
        return jsonify({"error": "Please provide a valid resume text or upload a PDF/TXT file."}), 400
        
    analysis = nlp_parser.analyze_resume(resume_text, target_role)
    return jsonify(analysis)

@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    message = data.get("message", "").strip()
    mode = data.get("mode", "general") # general, guidance, resume, placement
    session_id = data.get("session_id", "default_session")
    target_role = data.get("target_role", "Web Developer")
    
    if not message:
        return jsonify({"response": "I didn't receive any message. How can I help you today?"})

    # Initialize session history
    if session_id not in sessions:
        sessions[session_id] = []
        
    sessions[session_id].append({"sender": "user", "text": message})
    
    # Process response based on mode
    response_text = ""
    extra_data = {}
    
    # Simulated typing delay
    time.sleep(0.3)
    
    msg_lower = message.lower()
    
    # Check for general quick chip questions explicitly to ensure smart, ChatGPT-level responses
    if "what makes a strong portfolio" in msg_lower or "strong portfolio" in msg_lower:
        response_text = "🎯 **Building a Winning Professional Portfolio:**\n\n" \
                        "To stand out to recruiters, a strong portfolio should contain:\n" \
                        "1. **Host Live Demo Links:** Don't just show code. Host your projects on GitHub Pages, Vercel, Netlify, or Render so recruiters can interact with them instantly!\n" \
                        "2. **Write Premium READMEs:** A great project README has a clear title, description, screenshot/GIF, list of tech used, and instructions on how to install.\n" \
                        "3. **Showcase Unique Projects:** Avoid basic tutorial copies (like simple calculators). Build real-world solutions (e.g., e-commerce, student dashboards, or scraping engines).\n" \
                        "4. **GitHub Cleanliness:** Keep your repositories neat, commit regularly, and show a green contribution graph!\n\n" \
                        "What role are you targeting? I can suggest a customized portfolio project idea for you!"
                        
    elif "technologies are in demand" in msg_lower or "technologies in demand" in msg_lower or "in demand" in msg_lower:
        response_text = f"🔥 **Top In-Demand Technologies (2026):**\n\n" \
                        f"Depending on your **Target Path** (**{target_role}**), focus on these hot technologies:\n" \
                        f"* 🌐 **Web Development:** React, Next.js, TypeScript, TailwindCSS, Node.js, PostgreSQL, and GraphQL.\n" \
                        f"* 🧠 **AI / Machine Learning:** PyTorch, HuggingFace Transformers, LangChain (LLM integration), MLOps tools, and Python (Pandas/Numpy).\n" \
                        f"* 📊 **Data Analytics:** Advanced SQL, Power BI, Tableau, Python, Excel Pivot Tables, and Snowflake.\n" \
                        f"* 🛡️ **Cybersecurity:** Kali Linux, Wireshark, Cloud Security (AWS/Azure), SIEM systems, and Python/Bash scripting.\n\n" \
                        f"Currently, your target is set to **{target_role}**. Would you like a detailed learning roadmap for it?"

    elif "what is this bot for" in msg_lower or "what is this bot" in msg_lower:
        response_text = "🎓 **Welcome to CareerAI!**\n\n" \
                        "I am an intelligent Student Placement Assistant designed to solve real-world career preparation problems. I can:\n" \
                        "1. 🧭 **Career Guidance**: Run a Scikit-Learn Machine Learning text classifier to predict your optimal job role based on interests.\n" \
                        "2. 📄 **Resume Analyzer**: Use NLTK to parse your resume text/PDF, evaluate a compatibility score, and show skill gaps.\n" \
                        "3. 💼 **Placement Prep**: Serve mock interview questions, coding tips, aptitude advice, and soft skills guidance.\n\n" \
                        "Select any mode in the sidebar to begin!"

    elif "tell me about the tech roles" in msg_lower or "about the tech roles" in msg_lower:
        response_text = "💼 **Supported Industry Tech Roles:**\n\n" \
                        "1. 🌐 **Web Developer**: Builds interactive frontends and scalable servers. Critical skills: HTML, CSS, JS, React, Node.js, Databases.\n" \
                        "2. 🧠 **AI Engineer**: Develops ML models, neural networks, and LLMs. Critical skills: Python, PyTorch, Scikit-learn, NLP.\n" \
                        "3. 📊 **Data Analyst**: Transforms data into business insights and charts. Critical skills: SQL, Excel, Pandas, Power BI, Tableau.\n" \
                        "4. 🛡️ **Cybersecurity Analyst**: Secures networks and inspects threats. Critical skills: Linux, Firewalls, Wireshark, Cryptography.\n\n" \
                        "Which of these fits your personality best?"

    elif "explain the ml architecture" in msg_lower or "ml architecture" in msg_lower:
        response_text = "⚙️ **CareerAI Machine Learning & NLP Architecture:**\n\n" \
                        "1. **Natural Language Processing (NLP)**:\n" \
                        "   - Powered by **NLTK** (Natural Language Toolkit).\n" \
                        "   - Performs text cleaning, tokenization (`word_tokenize`), and cleans stopwords.\n" \
                        "   - Performs keyword extraction to calculate compatibility scores and list missing skill gaps.\n\n" \
                        "2. **Machine Learning (ML)**:\n" \
                        "   - Powered by **Scikit-Learn**.\n" \
                        "   - Uses **TF-IDF Vectorization** to convert raw interests/skills text into numerical features.\n" \
                        "   - Evaluates a **Logistic Regression** model (serialized via Pickle) to output confidence predictions per role."

    elif "how is the ats score calculated" in msg_lower or "ats score" in msg_lower:
        response_text = "📊 **ATS Score Calculation Breakdown:**\n\n" \
                        "Your ATS score is computed out of 100 using a professional weighted criteria:\n" \
                        "1. **Required Skill Match (70% weight)**: How many of the mandatory technical keywords for your target role are present in your resume.\n" \
                        "2. **Resume Length (15% weight)**: Checked via word count. An optimal ATS-readable resume is between 150 and 600 words.\n" \
                        "3. **Standard Section Titles (15% weight)**: Checks if your resume contains key standard headings (e.g., *Experience, Education, Projects, Skills, Contact*)."

    elif "list recommended keywords" in msg_lower or "recommended keywords" in msg_lower:
        skills = ", ".join(ROLE_PROFILES[target_role]["skills"])
        response_text = f"🔑 **Recommended Keywords for {target_role}:**\n\n" \
                        f"To achieve a high ATS score for the **{target_role}** role, ensure your resume contains these exact words:\n" \
                        f"`{skills.title()}`\n\n" \
                        f"Try adding these to your projects and experience descriptions!"

    elif "why are skills missing" in msg_lower or "missing skills" in msg_lower:
        response_text = "⚠ **Why does it say skills are missing?**\n\n" \
                        "Our NLTK keyword parser extracts terms from your resume and matches them against industry-standard requirements.\n" \
                        "If you know a skill but it's listed as missing, it means:\n" \
                        "1. You forgot to write it down on your resume.\n" \
                        "2. You used a different synonym or spelling.\n" \
                        "3. You haven't added projects showcasing that skill yet.\n\n" \
                        "Ensure you list all your skills explicitly to pass corporate ATS screens!"
                        
    if not response_text:
        if mode == "guidance":
        # Synonym mapping for industry roles
            from sklearn.feature_extraction.text import TfidfVectorizer
            from sklearn.metrics.pairwise import cosine_similarity

            # Training career intent dataset
            career_data = {
                "Web Developer": [
                    "I love building websites",
                    "I enjoy frontend design",
                    "I like creating web apps",
                    "I enjoy UI design",
                    "I love HTML CSS JavaScript",
                    "I want to become a web developer",
                    "I like designing interfaces"
                ],

                "AI Engineer": [
                    "I love machine learning",
                    "I enjoy artificial intelligence",
                    "I like deep learning",
                    "I enjoy coding AI models",
                    "I want to work with neural networks",
                    "I enjoy NLP and data science",
                    "I love automation"
                ],

                "Data Analyst": [
                    "I enjoy working with data",
                    "I love statistics",
                    "I like analyzing charts",
                    "I enjoy Excel and SQL",
                    "I like numbers and graphs",
                    "I enjoy business analytics",
                    "I like data visualization"
                ],

                "Cybersecurity Analyst": [
                    "I love ethical hacking",
                    "I enjoy network security",
                    "I like cybersecurity",
                    "I enjoy penetration testing",
                    "I like protecting systems",
                    "I enjoy Linux and security",
                    "I want to become a hacker"
                ]
            }

            # Build dataset
            all_sentences = []
            all_roles = []

            for role, texts in career_data.items():
                for text in texts:
                    all_sentences.append(text)
                    all_roles.append(role)

            # TF-IDF vectorizer
            vectorizer = TfidfVectorizer()

            X = vectorizer.fit_transform(all_sentences)

            # Convert user message
            user_vector = vectorizer.transform([message])

            # Calculate similarity
            similarity = cosine_similarity(user_vector, X)

            best_match_index = similarity.argmax()

            predicted_role = all_roles[best_match_index]

            confidence_score = round(similarity[0][best_match_index] * 100, 2)

            roadmap = ROLE_PROFILES[predicted_role]["roadmap"]

            skills_needed = ", ".join(
                ROLE_PROFILES[predicted_role]["skills"]
            )

            response_text = f"""
        🚀 Based on your interests, I predict that the best career path for you is:

        🎯 {predicted_role}

        📊 Confidence Score: {confidence_score}%

        💡 Important Skills Required:
        {skills_needed.title()}

        🗺️ Recommended Roadmap:
        """

            for idx, step in enumerate(roadmap, 1):
                response_text += f"\n{idx}. {step}"

            response_text += f"""

        🔥 Suggested Next Step:
        Start building projects related to {predicted_role} and strengthen your resume using the Resume Analyzer section.
        """

            # Extra frontend data
            predictions = ml_engine.predict_role(message)

            extra_data = {
                "predictions": predictions,
                "recommended_role": predicted_role
            }

        elif mode == "placement":
            if "question" in msg_lower or "interview" in msg_lower or "mock" in msg_lower:
                # Pick a sample question for this target role
                role_prep = PLACEMENT_PREP_POOL.get(target_role, PLACEMENT_PREP_POOL["Web Developer"])
                import random
                q_item = random.choice(role_prep["questions"])
                response_text = f"Here is a mock interview question for a **{target_role}** role:\n\n**Q: {q_item['q']}**\n\n*Think about your answer, then click or check below for the explanation!*\n\n||**Explanation:** {q_item['a']}||"
            elif "coding" in msg_lower or "code" in msg_lower:
                role_prep = PLACEMENT_PREP_POOL.get(target_role, PLACEMENT_PREP_POOL["Web Developer"])
                response_text = f"Here are some **Coding Preparation Tips** for **{target_role}**:\n\n{role_prep['coding_tips']}\n\n*Focus on learning complexity analysis (Big O) and core data structures!*"
            elif "aptitude" in msg_lower or "math" in msg_lower or "logic" in msg_lower:
                role_prep = PLACEMENT_PREP_POOL.get(target_role, PLACEMENT_PREP_POOL["Web Developer"])
                response_text = f"Here is your **Aptitude Guidance** for **{target_role}** placements:\n\n{role_prep['aptitude_tips']}"
            elif "communication" in msg_lower or "soft skill" in msg_lower or "tips" in msg_lower:
                role_prep = PLACEMENT_PREP_POOL.get(target_role, PLACEMENT_PREP_POOL["Web Developer"])
                response_text = f"Here is my **Communication Advice** to help you ace your interviews:\n\n{role_prep['communication_advice']}"
            else:
                response_text = f"Welcome to the Placement Assistant for **{target_role}**! I can help you with:\n\n1. **Interview Questions** (type 'mock question')\n2. **Coding Preparation** (type 'coding tips')\n3. **Aptitude Guidance** (type 'aptitude guidance')\n4. **Communication Advice** (type 'soft skills')\n\nWhat would you like to prepare first?"

        elif mode == "resume":
            # Case 1: User says they don't have a resume / no resume / don't have one
            if any(term in msg_lower for term in ["don't have a resume", "don't have one", "no resume", "don't have resume", "without resume", "do not have"]):
                response_text = f"No worries at all! You do not need a pre-existing resume file to get started. I can help you **build one from scratch** right here!\n\n" \
                                f"Let's draft a professional resume for your target path (**{target_role}**). To begin, tell me:\n" \
                                f"1. What is your major/degree (e.g., B.Tech in CS or BCA)?\n" \
                                f"2. Any specific programming tools or technologies you have worked with?\n" \
                                f"3. Have you done any small academic or hobby projects?\n\n" \
                                f"Reply with these details, and I will write a customized resume structure and professional summary for you!"
            
            # Case 2: User mentions they want to create/write/make/build a resume
            elif any(term in msg_lower for term in ["create", "build", "write", "make", "draft", "guideline", "template"]) and "resume" in msg_lower:
                response_text = f"Sure! Here are standard industry guidelines to write an outstanding **{target_role}** resume:\n\n" \
                                f"1. **Professional Summary:** A 3-sentence elevator pitch highlighting your core target field, key skills, and career motivation.\n" \
                                f"2. **Core Skills Section:** Bullet list of exact technical keywords matching the role (e.g., " + ", ".join(ROLE_PROFILES[target_role]["skills"][:6]).title() + ").\n" \
                                f"3. **Academic/Hobby Projects:** 2 substantial projects with descriptions explaining your contribution, tech stack used, and the final impact.\n" \
                                f"4. **Education & Certifications:** Include your university, graduation year, and certifications.\n\n" \
                                f"Would you like me to generate a tailored **resume template** for a **{target_role}**? Just type 'give me a template'!"
                            
            # Case 3: User wants a template generated
            elif "template" in msg_lower and ("resume" in msg_lower or "cv" in msg_lower):
                skills_needed = ", ".join(ROLE_PROFILES[target_role]["skills"])
                response_text = f"Here is a professional, ATS-friendly resume template for a **{target_role}**:\n\n" \
                                f"```\n" \
                                f"[YOUR NAME] | [PHONE] | [EMAIL] | [LINKEDIN/GITHUB]\n\n" \
                                f"PROFESSIONAL SUMMARY\n" \
                                f"Motivated computer science student aspiring to become a professional {target_role}. " \
                                f"Skilled in modern concepts and eager to apply technical knowledge in a fast-paced team.\n\n" \
                                f"CORE TECHNICAL SKILLS\n" \
                                f"* Technologies: {skills_needed.title()}\n\n" \
                                f"ACADEMIC PROJECTS\n" \
                                f"* Project 1: [Title]\n" \
                                f"  - Built a system using [Tech Stack] to solve [Problem].\n" \
                                f"  - Achieved [Metric/Result].\n\n" \
                                f"EDUCATION\n" \
                                f"* Bachelor of Technology / Science | [University] | [GPA/Percentage] (Expected 2026)\n" \
                                f"```\n\n" \
                                f"Feel free to copy and edit this template with your details! Once ready, paste it in the **Resume Analyzer** panel on the right to calculate your real-time NLTK ATS score!"
            
            # Case 4: The user pastes their resume text in chat
            elif len(nlp_parser.extract_skills_and_clean(message)) >= 3 or any(term in msg_lower for term in ["experience", "education", "project", "summary", "contact"]):
                analysis = nlp_parser.analyze_resume(message, target_role)
                response_text = f"📊 **Real-time Resume Analysis Complete!**\n\n" \
                                f"I parsed your pasted text against the **{target_role}** requirements:\n" \
                                f"- **NLTK ATS Score:** **{analysis['ats_score']}/100**\n" \
                                f"- **Extracted Skills:** {', '.join(analysis['extracted_skills']).title() if analysis['extracted_skills'] else 'None'}\n" \
                                f"- **Matched Required Skills:** {', '.join(analysis['matching_skills']).title() if analysis['matching_skills'] else 'None'}\n" \
                                f"- **Missing Core Skills:** {', '.join(analysis['missing_skills']).title() if analysis['missing_skills'] else 'None'}\n\n" \
                                f"🗺️ **Roadmap to cover missing skills:\n"
                for idx, step in enumerate(analysis['roadmap'], 1):
                    response_text += f"{idx}. {step}\n"
                response_text += f"\n*Tip: You can also use the file upload card in the panel on the right to upload your direct PDF or TXT resume!*"
            
            # Case 5: Standard fallback
            else:
                skills_extracted = nlp_parser.extract_skills_and_clean(message)
                if skills_extracted:
                    response_text = f"I detected these skills in your message: **{', '.join(skills_extracted).title()}**.\n\n" \
                                    f"To check how they match against your target path (**{target_role}**), try pasting your full resume details here, or use the **Resume Analyzer** panel on the right to upload your PDF file and compute a full ATS score!"
                else:
                    response_text = f"You are in **Resume Analyzer** mode for **{target_role}**.\n\n" \
                                    f"What would you like to do?\n" \
                                    f"1. Tell me **'I don't have a resume'** to build one from scratch.\n" \
                                    f"2. Paste your resume text directly into this chat to get a real-time NLTK score.\n" \
                                    f"3. Drag and drop your resume file in the dashboard card on the right!"


        else: # general mode
            if any(greet in msg_lower for greet in ["hello", "hi", "hey", "greetings", "yo", "howdy", "sup"]):
                response_text = "Hello! I am your AI Career Guidance & Placement Assistant. I am here to help you parse your resume, find missing skills, predict your dream job roles, and prepare for placement interviews. Where shall we start? Select a tool in the sidebar or just ask me anything!"

            elif "help" in msg_lower or "what can you do" in msg_lower or "features" in msg_lower:
                response_text = "🛠️ **Here is everything I can do for you:**\n\n" \
                                "1. 🧭 **Career Guidance** — Tell me your interests and I will run a ML model to predict your ideal job role with a confidence score.\n" \
                                "2. 📄 **Resume Analyzer** — Paste your resume or upload a PDF. I will extract your skills, calculate your ATS score, and show you exactly what is missing.\n" \
                                "3. 💼 **Placement Prep** — Request mock interview questions, coding tips, aptitude guidance, or communication strategies for your target role.\n\n" \
                                "Switch modes using the **sidebar** or keep chatting here — I understand natural language!\n\n" \
                                "💡 **Quick tip:** Type `'Explain the ML architecture'` to learn how this app is built!"

            elif any(word in msg_lower for word in ["career", "job", "role", "path", "field", "which job", "choose career", "career advice", "career path"]):
                response_text = f"🧭 **Career Path Advice:**\n\n" \
                                f"Choosing the right career is the most important decision in your professional journey. Here's how to figure it out:\n\n" \
                                f"1. **Identify your strengths:** Are you more analytical (→ Data Analyst), creative (→ Web Developer), security-focused (→ Cybersecurity), or research-oriented (→ AI Engineer)?\n" \
                                f"2. **Try the Career Guidance mode:** Switch to **Career Guidance** in the sidebar and describe your interests — our ML model will predict the best role for you with a confidence score!\n" \
                                f"3. **Explore roadmaps:** Each role has a curated learning roadmap to go from beginner to job-ready.\n\n" \
                                f"Your current target path is set to **{target_role}**. Would you like a detailed roadmap for it? Just ask!"

            elif any(word in msg_lower for word in ["resume", "cv", "curriculum vitae", "ats", "ats score", "application"]):
                response_text = f"📄 **Resume Tips for {target_role}:**\n\n" \
                                f"A strong resume is your ticket to getting past the automated ATS systems that most companies use.\n\n" \
                                f"🔑 **Key Resume Rules:**\n" \
                                f"- **Use exact keywords**: Companies search for specific terms. For {target_role}, make sure you include: `{', '.join(ROLE_PROFILES[target_role]['skills'][:5]).title()}`\n" \
                                f"- **Keep it 1 page** (for freshers) with clean formatting.\n" \
                                f"- **Quantify achievements**: 'Improved load speed by 40%' is stronger than 'Improved the website'.\n" \
                                f"- **Add a GitHub/Portfolio link** — recruiters love seeing live work!\n\n" \
                                f"Switch to **Resume Analyzer** mode to paste your resume text and get a real-time ATS score out of 100!"

            elif any(word in msg_lower for word in ["interview", "prepare", "preparation", "mock", "question", "hr round", "technical round"]):
                response_text = f"💼 **Interview Preparation Guide for {target_role}:**\n\n" \
                                f"Cracking interviews requires structured preparation. Here's your game plan:\n\n" \
                                f"📌 **Stages of a Typical Tech Interview:**\n" \
                                f"1. **Online Assessment (OA):** Aptitude, basic coding problems (30-60 min).\n" \
                                f"2. **Technical Round 1:** DSA problems + core technical questions about your role.\n" \
                                f"3. **Technical Round 2:** System design / project deep-dive.\n" \
                                f"4. **HR Round:** Behavioral questions (STAR method), salary discussion, culture fit.\n\n" \
                                f"💡 Switch to **Placement Prep** mode and type `'mock question'` to get a real practice question for **{target_role}**!"

            elif any(word in msg_lower for word in ["salary", "package", "ctc", "pay", "lpa", "earning", "income"]):
                response_text = "💰 **Fresher Salary Ranges in India (2026):**\n\n" \
                                "| Role | Entry-Level CTC | Top Companies |\n" \
                                "|------|----------------|---------------|\n" \
                                "| Web Developer | ₹3 – ₹8 LPA | TCS, Infosys, Startups |\n" \
                                "| Data Analyst | ₹4 – ₹9 LPA | Deloitte, Wipro, MNCs |\n" \
                                "| AI Engineer | ₹6 – ₹18 LPA | Google, Microsoft, FAANG |\n" \
                                "| Cybersecurity Analyst | ₹4 – ₹12 LPA | IBM, Cisco, Banks |\n\n" \
                                "💡 **Tip:** Salaries scale significantly with strong GitHub portfolios and certifications like AWS, Azure, or Google Cloud!"

            elif any(word in msg_lower for word in ["learn", "study", "course", "certification", "roadmap", "how to start", "beginner", "getting started"]):
                roadmap = ROLE_PROFILES.get(target_role, {}).get("roadmap", [])
                response_text = f"📚 **Learning Roadmap for {target_role}:**\n\n" \
                                f"Here is a step-by-step path to become job-ready as a **{target_role}**:\n\n"
                if roadmap:
                    for idx, step in enumerate(roadmap, 1):
                        response_text += f"{idx}. {step}\n"
                else:
                    response_text += "Switch to **Career Guidance** mode for a personalized roadmap based on your interests!\n"
                response_text += f"\n🎯 **Recommended Free Resources:**\n" \
                                 f"- [freeCodeCamp](https://freecodecamp.org) | [The Odin Project](https://theodinproject.com) | [Kaggle](https://kaggle.com) | [TryHackMe](https://tryhackme.com)\n\n" \
                                 f"After studying, upload your resume in **Resume Analyzer** mode to check how job-ready you really are!"

            elif any(word in msg_lower for word in ["skill", "skills", "technologies", "tools", "programming language", "language", "tech stack"]):
                skills_list = ROLE_PROFILES.get(target_role, {}).get("skills", [])
                response_text = f"🔧 **Top Skills for {target_role} (2026):**\n\n" \
                                f"Based on current job market trends, a **{target_role}** should master:\n\n"
                for skill in skills_list:
                    response_text += f"✅ **{skill.title()}**\n"
                response_text += f"\n💡 Use the **Resume Analyzer** to see which of these skills are already on your resume and which ones you are missing!"

            elif any(word in msg_lower for word in ["project", "projects", "portfolio", "side project", "build", "app idea"]):
                response_text = f"🚀 **Project Ideas for {target_role} Portfolio:**\n\n" \
                                f"Building real projects is the #1 way to impress recruiters. Here are some ideas specific to **{target_role}**:\n\n"
                project_ideas = {
                    "Web Developer": ["🛒 E-Commerce Store with cart & payment integration", "📋 Task Manager with drag-and-drop (React + Node.js)", "🌐 Personal Portfolio with animations (GSAP/Framer Motion)", "💬 Real-time Chat App using WebSockets"],
                    "AI Engineer": ["🤖 Movie Recommendation System using Collaborative Filtering", "🖼️ Image Classifier using TensorFlow/PyTorch CNN", "📰 Fake News Detector using NLP (BERT)", "💬 Custom Chatbot using HuggingFace Transformers"],
                    "Data Analyst": ["📊 Sales Dashboard with Tableau/Power BI", "🏏 IPL/Cricket Stats Explorer using Pandas + Plotly", "🏠 House Price Predictor using Linear Regression", "📈 Stock Market Trend Visualizer with Python"],
                    "Cybersecurity Analyst": ["🔍 Network Port Scanner using Python Sockets", "🔐 Password Strength Checker & Generator", "🛡️ Simple IDS (Intrusion Detection System) with ML", "📱 Phishing URL Detector using NLP"]
                }
                ideas = project_ideas.get(target_role, project_ideas["Web Developer"])
                for idea in ideas:
                    response_text += f"- {idea}\n"
                response_text += f"\n🔑 **Pro Tip:** Always deploy your projects live (Vercel/Netlify/Render) and write a detailed README on GitHub!"

            elif any(word in msg_lower for word in ["company", "companies", "google", "microsoft", "amazon", "facebook", "meta", "tcs", "infosys", "startup", "product", "service"]):
                response_text = "🏢 **Types of Companies to Target:**\n\n" \
                                "**1. 🏗️ Service-Based (Mass Hiring) — TCS, Infosys, Wipro, Accenture**\n" \
                                "- Hire in bulk from campuses. Focus on: aptitude, communication, basic coding.\n" \
                                "- Packages: ₹3.5 – ₹7 LPA for freshers.\n\n" \
                                "**2. 💡 Product-Based (Dream Companies) — Google, Microsoft, Amazon, Flipkart**\n" \
                                "- Hire for strong DSA, system design, and problem solving.\n" \
                                "- Packages: ₹15 – ₹40+ LPA for freshers.\n\n" \
                                "**3. 🚀 Startups — Zepto, Razorpay, Groww, CRED**\n" \
                                "- Hire generalists who can build fast. Focus on: ownership, project work, full-stack skills.\n" \
                                "- Packages: ₹5 – ₹25 LPA with equity options.\n\n" \
                                "💡 **Tip:** Apply to all three categories in parallel. Use LinkedIn, Unstop, Naukri, and AngelList!"

            else:
                # Smart fallback — acknowledge their message and guide them
                response_text = f"🤔 Great question! Here's how I can help you with that:\n\n" \
                                f"As your AI Career Assistant, I specialize in **career guidance, resume analysis, and placement preparation** for tech roles.\n\n" \
                                f"Try asking me things like:\n" \
                                f"- *\"What skills do I need for {target_role}?\"*\n" \
                                f"- *\"Give me a learning roadmap\"*\n" \
                                f"- *\"What are good project ideas?\"*\n" \
                                f"- *\"How much salary can I expect?\"*\n" \
                                f"- *\"How do I prepare for interviews?\"*\n\n" \
                                f"Or switch to a specialized mode using the sidebar: **Career Guidance**, **Resume Analyzer**, or **Placement Prep**!"

    sessions[session_id].append({"sender": "bot", "text": response_text})
    
    return jsonify({
        "response": response_text,
        "mode": mode,
        "session_id": session_id,
        "extra": extra_data
    })

@app.route("/api/chat/<session_id>", methods=["DELETE"])
def clear_chat(session_id):
    if session_id in sessions:
        sessions[session_id] = []
    return jsonify({"status": "cleared", "session_id": session_id})

import os
from flask import send_from_directory
@app.route("/")
def home():
    return send_from_directory("../frontend", "index.html")
@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('../frontend', path)
if __name__ == "__main__":
    print("Launching Flask Server...")
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000))
    )
