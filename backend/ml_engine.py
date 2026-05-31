import os
import pickle
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

# Custom training dataset mapping skills, interests, and strengths to 4 core student career paths.
TRAINING_DATA = [
    # Data Analyst
    ("python sql pandas numpy powerbi tableau data analytics dashboard statistics data mining visualization excel sql server business intelligence graphs reports chart postgresql", "Data Analyst"),
    ("i like analyzing data databases statistics dashboards sql query pandas power bi reports data science dashboard business trends analytical thinking forecasting mathematical modeling math", "Data Analyst"),
    ("excel spreadsheets databases business analysts tableu chart visualizations database administration mining pattern recognition business growth optimization pivot tables data modeling", "Data Analyst"),
    ("quantitative analysis sql data extraction clean data python libraries analytics sql queries visualization business logic powerbi tableau analysis statistics math numerical database", "Data Analyst"),
    
    # AI Engineer
    ("python machine learning deep learning neural networks pytorch tensorflow artificial intelligence nlp computer vision scikit-learn transformers llms transformers chatbot keras scikit classification", "AI Engineer"),
    ("i want to build ai models train neural networks chatbots natural language processing speech recognition computer vision huggingface transformers reinforcement learning intelligent systems deeplearning pytorch", "AI Engineer"),
    ("ai machine learning classification modeling generative ai algorithms linear algebra probability predictive modeling logic reasoning robotics python code optimization keras sklearn datasets", "AI Engineer"),
    ("tensorflow model deployment object detection sentiment analysis image classification clustering automation deep learning python data-science mathematical AI neural-net huggingface", "AI Engineer"),

    # Web Developer
    ("html css javascript react vue angular nodejs express bootstrap tailwind sass web development frontend backend fullstack website dynamic interfaces client-server html5 css3 javascript-es6", "Web Developer"),
    ("building website design ui ux user interface front-end back-end developer node express databases reactjs nextjs website designer web apps frontend developer web design coding projects", "Web Developer"),
    ("javascript web engineer web dev front-end design web browser interfaces custom css modern ui widgets typescript chrome dev api integration rest api endpoint web development templates css3", "Web Developer"),
    ("full stack developer mern stack node.js express mongodb react native app development web application server coding vanilla js responsive layout flexbox grid animation website design", "Web Developer"),

    # Cybersecurity Analyst
    ("cybersecurity penetration testing ethical hacking cryptography firewalls network security encryption linux wireshark information security vulnerability assessment security audit ports hacking", "Cybersecurity Analyst"),
    ("i love security networks network defense cryptography ethical hacker bash scripting linux terminal ports tracking firewalls prevention vulnerability scanning intrusion detection malware analysis proxy", "Cybersecurity Analyst"),
    ("cyber security protocols digital forensics encryption systems administration network architecture compliance audit risk management penetration tester hack defensive security secure systems wireshark", "Cybersecurity Analyst"),
    ("network protocols infrastructure access control malware prevention threat hunting pen testing linux kali linux cloud security network security defense cryptography encryption audit incident response", "Cybersecurity Analyst")
]

MODEL_PATH = os.path.join(os.path.dirname(__file__), "career_model.pkl")
VECTORIZER_PATH = os.path.join(os.path.dirname(__file__), "vectorizer.pkl")

class MLEngine:
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.trained = False
        self.initialize_model()

    def train_model(self):
        """Train a TF-IDF + Logistic Regression pipeline on the local training set."""
        print("Training Job Role Prediction model...")
        
        texts = [item[0] for item in TRAINING_DATA]
        labels = [item[1] for item in TRAINING_DATA]

        # Convert texts to lowercase TF-IDF features
        self.vectorizer = TfidfVectorizer(lowercase=True, stop_words='english', ngram_range=(1, 2))
        x_train = self.vectorizer.fit_transform(texts)
        
        # Train a Logistic Regression model
        # Use high C for stronger fit on our small, clean dataset
        self.model = LogisticRegression(C=10.0, max_iter=200)
        self.model.fit(x_train, labels)
        
        # Serialize model & vectorizer
        try:
            with open(MODEL_PATH, "wb") as f:
                pickle.dump(self.model, f)
            with open(VECTORIZER_PATH, "wb") as f:
                pickle.dump(self.vectorizer, f)
            self.trained = True
            print("Model trained and saved successfully.")
        except Exception as e:
            print(f"Error saving model: {e}")

    def initialize_model(self):
        """Load the pre-trained model or train a new one if files do not exist."""
        if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
            try:
                with open(MODEL_PATH, "rb") as f:
                    self.model = pickle.load(f)
                with open(VECTORIZER_PATH, "rb") as f:
                    self.vectorizer = pickle.load(f)
                self.trained = True
                print("Model loaded from disk.")
            except Exception as e:
                print(f"Error loading model: {e}. Retraining...")
                self.train_model()
        else:
            self.train_model()

    def predict_role(self, input_text):
        """
        Takes raw skills/interests/strengths text, vectorizes it, and runs classifier.
        Returns a sorted list of dictionaries with 'role' and 'confidence' (percentage).
        """
        if not self.trained or self.model is None or self.vectorizer is None:
            self.initialize_model()

        # Vectorize input
        x_input = self.vectorizer.transform([input_text.lower()])
        
        # Predict probabilities
        probabilities = self.model.predict_proba(x_input)[0]
        classes = self.model.classes_
        
        results = []
        for cls, prob in zip(classes, probabilities):
            results.append({
                "role": cls,
                "confidence": round(float(prob) * 100, 1)
            })
            
        # Sort by confidence descending
        results = sorted(results, key=lambda x: x["confidence"], reverse=True)
        return results

# Self-test block when run directly
if __name__ == "__main__":
    engine = MLEngine()
    test_text = "I love making reactive websites using HTML, CSS, JavaScript, React and nodejs"
    predictions = engine.predict_role(test_text)
    print(f"\nTest text: '{test_text}'")
    for p in predictions:
        print(f"- {p['role']}: {p['confidence']}%")
