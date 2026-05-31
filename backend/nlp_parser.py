import re
import nltk
from nltk.tokenize import word_tokenize

# NLTK resources setup
for resource in ['punkt', 'punkt_tab']:
    try:
        if resource == 'punkt':
            nltk.data.find('tokenizers/punkt')
        else:
            nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        nltk.download(resource, quiet=True)


# Standard skills lookup list by role
ROLE_PROFILES = {
    "Data Analyst": {
        "skills": ["python", "sql", "pandas", "numpy", "tableau", "power bi", "excel", "statistics", "data visualization", "r", "databases", "analytics", "mysql", "postgresql", "dashboard"],
        "roadmap": [
            "Learn Python programming and core libraries (Pandas, Numpy, Matplotlib)",
            "Master SQL for database querying and data wrangling",
            "Learn a Data Visualization tool (Tableau or Power BI) to build dashboards",
            "Study exploratory data analysis (EDA) and basic business statistics",
            "Work on a hands-on project analyzing public datasets (e.g., Kaggle)"
        ]
    },
    "AI Engineer": {
        "skills": ["python", "machine learning", "deep learning", "pytorch", "tensorflow", "scikit-learn", "nlp", "computer vision", "neural networks", "keras", "sql", "git", "huggingface", "llm", "ai"],
        "roadmap": [
            "Strong foundation in Python and linear algebra, calculus, & probability",
            "Learn Scikit-Learn for standard Machine Learning algorithms (regression, classification, clustering)",
            "Master Deep Learning architectures (CNNs, RNNs, Transformers) using PyTorch or TensorFlow",
            "Specialize in an AI domain (Natural Language Processing or Computer Vision)",
            "Build and deploy models using APIs (FastAPI/Flask) and cloud servers"
        ]
    },
    "Web Developer": {
        "skills": ["html", "css", "javascript", "react", "nodejs", "express", "mongodb", "git", "bootstrap", "tailwind css", "typescript", "apis", "nextjs", "vue", "angular", "rest api"],
        "roadmap": [
            "Master Semantic HTML5, responsive CSS3 grids, and CSS flexbox layouts",
            "Learn Modern JavaScript (ES6+), DOM manipulation, and asynchronous programming (Fetch/Promises)",
            "Learn Git & GitHub for version control and collaborating",
            "Specialize in a modern frontend framework (React, Vue, or Angular)",
            "Learn backend development (Node.js/Express) and database querying (MongoDB/PostgreSQL) to become Fullstack"
        ]
    },
    "Cybersecurity Analyst": {
        "skills": ["cybersecurity", "linux", "networking", "firewalls", "wireshark", "penetration testing", "ethical hacking", "cryptography", "threat hunting", "siem", "owasp", "incident response", "bash", "active directory"],
        "roadmap": [
            "Understand computer networking fundamentals (TCP/IP model, routing, switching, DNS)",
            "Get comfortable with Linux operating systems and CLI shell scripting",
            "Learn active defense strategies including Firewalls, Intrusion Detection Systems (IDS/IPS), and SIEM tools",
            "Study Cryptography concepts (symmetric/asymmetric encryption, hashing)",
            "Obtain foundational certifications (CompTIA Security+, CEH) and practice labs on TryHackMe or HackTheBox"
        ]
    }
}

# Flat set of all skills for general extraction
ALL_SKILLS = set(skill for profile in ROLE_PROFILES.values() for skill in profile["skills"])

class NLPParser:
    def __init__(self):
        pass

    def extract_skills_and_clean(self, text):
        """
        Cleans text, tokenizes, and extracts matches from our comprehensive skills dictionary.
        Returns a sorted list of unique extracted skills.
        """
        # Lowercase and remove punctuation
        text_clean = re.sub(r'[^\w\s\+\#\-]', ' ', text.lower())
        tokens = word_tokenize(text_clean)
        
        extracted = set()
        
        # Exact matching from tokens (e.g. 'python', 'react')
        for t in tokens:
            if t in ALL_SKILLS:
                extracted.add(t)
                
        # Multi-word matching (e.g., 'power bi', 'tailwind css', 'machine learning', 'deep learning')
        text_collapsed = " ".join(tokens)
        multi_word_skills = ["power bi", "tailwind css", "machine learning", "deep learning", "computer vision", "neural networks", "penetration testing", "ethical hacking", "threat hunting", "incident response", "active directory", "data visualization", "rest api"]
        
        for ms in multi_word_skills:
            if ms in text_collapsed:
                extracted.add(ms)
                
        return sorted(list(extracted))

    def analyze_resume(self, resume_text, target_role):
        """
        Analyzes resume text against a target career path.
        Computes ATS score, matching skills, and missing skills.
        """
        if target_role not in ROLE_PROFILES:
            target_role = "Web Developer"  # Default fallback
            
        role_info = ROLE_PROFILES[target_role]
        required_skills = role_info["skills"]
        
        # Extract skills present in resume
        my_extracted_skills = self.extract_skills_and_clean(resume_text)
        
        # Calculate skills present that are required for this role
        matching_skills = [s for s in my_extracted_skills if s in required_skills]
        missing_skills = [s for s in required_skills if s not in my_extracted_skills]
        
        # Compute ATS Score logic
        # 1. Skill Match Score (weight = 70%): fraction of target skills present
        skill_match_ratio = len(matching_skills) / len(required_skills) if required_skills else 0
        skill_score = skill_match_ratio * 70
        
        # 2. Structure & Length Score (weight = 30%): checking word count and professional headings
        word_count = len(resume_text.split())
        length_score = 0
        if 150 <= word_count <= 600:
            length_score += 15  # Optimal resume length for ATS readability
        elif word_count > 0:
            length_score += 8
            
        # Check standard sections
        sections = ["experience", "education", "project", "skills", "certifications", "contact", "summary"]
        section_count = 0
        for sec in sections:
            if sec in resume_text.lower():
                section_count += 1
        
        structure_score = (section_count / len(sections)) * 15
        
        total_ats_score = round(skill_score + length_score + structure_score)
        total_ats_score = min(100, max(15, total_ats_score)) # clamp between 15 and 100
        
        return {
            "target_role": target_role,
            "ats_score": total_ats_score,
            "matching_skills": matching_skills,
            "missing_skills": missing_skills,
            "extracted_skills": my_extracted_skills,
            "roadmap": role_info["roadmap"]
        }

# Self-test block when run directly
if __name__ == "__main__":
    parser = NLPParser()
    resume = """
    John Doe - AI Engineer Resume
    CONTACT: john.doe@email.com
    SUMMARY: Enthusiastic computer science student with a focus on Artificial Intelligence and Machine Learning.
    SKILLS: Python, SQL, Git, PyTorch, Deep Learning, HTML, CSS.
    EXPERIENCE: 
    - Built classification models in Python using PyTorch and Scikit-learn.
    - Designed neural networks for sentiment analysis.
    PROJECTS:
    - Object detection system using TensorFlow.
    """
    analysis = parser.analyze_resume(resume, "AI Engineer")
    print(f"ATS SCORE: {analysis['ats_score']}/100")
    print(f"Matching: {analysis['matching_skills']}")
    print(f"Missing: {analysis['missing_skills']}")
