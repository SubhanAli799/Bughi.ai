# ============================================
# BUG HUNTING AI - OFFLINE VERSION
# ============================================
# Fully offline, local data storage, smooth working
# ============================================

import os
import sys
import json
import time
import requests
import sqlite3
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ============================================
# AUTO-INSTALL MISSING PACKAGES
# ============================================

def auto_install():
    """Auto install missing packages"""
    required = ['transformers', 'torch', 'gradio', 'accelerate']
    missing = []
    
    for pkg in required:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    
    if missing:
        print(f"📦 Installing: {', '.join(missing)}")
        for pkg in missing:
            os.system(f"{sys.executable} -m pip install {pkg} -q")
        print("✅ All packages installed!")

auto_install()

# ============================================
# IMPORTS
# ============================================

import torch
import gradio as gr
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

print("🛡️ Bug Hunting AI - Offline Edition")
print("=" * 50)

# ============================================
# LOCAL DATA STORAGE
# ============================================

class LocalStorage:
    def __init__(self):
        self.data_dir = "./data"
        self.db_path = os.path.join(self.data_dir, "history.db")
        self.json_path = os.path.join(self.data_dir, "history.json")
        
        # Create data directory
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize database
        self.init_db()
    
    def init_db(self):
        """Initialize SQLite database"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                question TEXT,
                response TEXT,
                type TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def save(self, question, response, type="chat"):
        """Save to local storage"""
        timestamp = datetime.now().isoformat()
        
        # Save to SQLite
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO history (timestamp, question, response, type) VALUES (?, ?, ?, ?)",
            (timestamp, question, response, type)
        )
        conn.commit()
        conn.close()
        
        # Also save to JSON
        self.save_to_json(question, response, type)
    
    def save_to_json(self, question, response, type):
        """Save to JSON file"""
        data = []
        if os.path.exists(self.json_path):
            with open(self.json_path, 'r') as f:
                try:
                    data = json.load(f)
                except:
                    data = []
        
        data.append({
            'timestamp': datetime.now().isoformat(),
            'question': question,
            'response': response,
            'type': type
        })
        
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_history(self, limit=50):
        """Get chat history"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            "SELECT timestamp, question, response, type FROM history ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        rows = c.fetchall()
        conn.close()
        
        if rows:
            return [f"[{row[0]}] {row[1]}\n{row[2]}\n" for row in rows]
        return ["No history found."]
    
    def clear_history(self):
        """Clear all history"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("DELETE FROM history")
        conn.commit()
        conn.close()
        
        if os.path.exists(self.json_path):
            os.remove(self.json_path)
        
        return "✅ History cleared!"

# Initialize local storage
storage = LocalStorage()

# ============================================
# LOAD MODEL (LOCALLY CACHED)
# ============================================

MODEL_ID = "Subhan162/bug-hunting-ai"
CACHE_DIR = "./models"

print(f"📥 Loading model: {MODEL_ID}")
print("💾 Model will be cached locally at:", CACHE_DIR)

pipe = None

def load_model():
    global pipe
    try:
        # Create cache directory
        os.makedirs(CACHE_DIR, exist_ok=True)
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            MODEL_ID,
            cache_dir=CACHE_DIR,
            trust_remote_code=True
        )
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            cache_dir=CACHE_DIR,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True,
        )
        
        # Create pipeline
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=400,
            do_sample=True,
            temperature=0.7,
            pad_token_id=tokenizer.eos_token_id,
        )
        print("✅ Model loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("🔄 Using lightweight fallback...")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained("gpt2", cache_dir=CACHE_DIR)
            tokenizer.pad_token = tokenizer.eos_token
            model = AutoModelForCausalLM.from_pretrained("gpt2", cache_dir=CACHE_DIR)
            pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
            print("✅ Fallback model loaded!")
            return True
        except:
            print("❌ Failed to load model!")
            return False

# Load model
model_loaded = load_model()

# ============================================
# TOOL FUNCTIONS
# ============================================

def analyze_cve(cve_id: str) -> str:
    """Analyze CVE with local storage"""
    if not cve_id:
        return "⚠️ Enter CVE ID"
    
    prompt = f"Analyze {cve_id} vulnerability with description, impact, and mitigation:"
    
    try:
        if pipe is None:
            return "❌ Model not loaded"
        
        result = pipe(prompt, max_new_tokens=500)
        response = result[0]['generated_text']
        
        # Save to local storage
        storage.save(cve_id, response, "cve")
        
        return response
    except Exception as e:
        return f"❌ Error: {str(e)}"

def fetch_cves(limit: str = "5") -> str:
    """Fetch CVEs from NVD (requires internet)"""
    try:
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {"resultsPerPage": int(limit)}
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        cves = []
        for cve in data.get('vulnerabilities', [])[:int(limit)]:
            cve_data = cve.get('cve', {})
            cves.append(f"📌 {cve_data.get('id', 'N/A')}")
        
        result = "📋 Latest CVEs:\n" + "\n".join(cves)
        storage.save(f"fetch {limit} cves", result, "fetch")
        return result
    except:
        return "⚠️ Internet needed for this feature"

def scan_website(url: str) -> str:
    """Scan website (requires internet)"""
    if not url.startswith('http'):
        url = 'https://' + url
    
    try:
        response = requests.get(url, timeout=10)
        result = f"🔍 Scan: {url}\n📊 Status: {response.status_code}\n📏 Size: {len(response.text)} bytes"
        storage.save(f"scan {url}", result, "scan")
        return result
    except Exception as e:
        return f"❌ Error: {e}"

def review_code(code: str) -> str:
    """Review code with local AI"""
    if len(code) < 5:
        return "⚠️ Provide code"
    
    prompt = f"Review code for security issues:\n{code}"
    
    try:
        if pipe is None:
            return "❌ Model not loaded"
        
        result = pipe(prompt, max_new_tokens=400)
        response = result[0]['generated_text']
        storage.save("code_review", response, "code")
        return response
    except Exception as e:
        return f"❌ Error: {str(e)}"

def process_query(query: str) -> str:
    """Process all queries"""
    if not query:
        return "⚠️ Enter question"
    
    q = query.lower().strip()
    
    # Check if query is a command
    if q.startswith("analyze"):
        cve = query.split("analyze")[-1].strip()
        return analyze_cve(cve) if cve else "⚠️ Enter CVE ID"
    
    elif q.startswith("fetch"):
        parts = query.split()
        limit = parts[1] if len(parts) > 1 else "5"
        return fetch_cves(limit)
    
    elif q.startswith("scan"):
        url = query.split("scan")[-1].strip()
        return scan_website(url) if url else "⚠️ Enter URL"
    
    elif q.startswith("review code"):
        code = query.split("review code")[-1].strip()
        return review_code(code) if code else "⚠️ Enter code"
    
    elif q in ["history", "h"]:
        return "\n".join(storage.get_history(10))
    
    elif q in ["clear", "c"]:
        return storage.clear_history()
    
    elif q in ["help", "?"]:
        return """
📋 Commands:
analyze CVE-ID    → Analyze CVE (offline)
fetch N cves      → Latest CVEs (online)
scan URL          → Scan website (online)
review code CODE  → Code review (offline)
history           → Show history
clear             → Clear history
help              → Show this menu
Any question      → AI answers
"""
    
    else:
        # AI Chat
        try:
            if pipe is None:
                return "❌ Model not loaded"
            
            result = pipe(query, max_new_tokens=300)
            response = result[0]['generated_text']
            
            # Save to local storage
            storage.save(query, response, "chat")
            
            return response
        except Exception as e:
            return f"❌ Error: {str(e)}"

# ============================================
# GRADIO INTERFACE
# ============================================

SUGGESTIONS = [
    "analyze CVE-2024-6387",
    "fetch 5 cves",
    "scan https://example.com",
    "What is SQL injection?",
    "review code def login():",
    "history",
    "help",
]

def create_interface():
    with gr.Blocks(title="🔍 Bug Hunting AI - Offline", theme=gr.themes.Soft()) as demo:
        
        gr.Markdown("""
        # 🔍 Bug Hunting AI - Offline Edition
        ### 💾 All data saved locally | No server needed
        """)
        
        # Status
        status = "✅ Model Loaded" if pipe is not None else "⚠️ Fallback Mode"
        gr.Markdown(f"**Status:** {status} | **Data:** Local SQLite + JSON")
        
        with gr.Row():
            with gr.Column(scale=4):
                query = gr.Textbox(
                    label="🔎 Search",
                    placeholder="analyze CVE-2024-6387 or What is SQL injection?",
                    lines=2,
                )
                
                with gr.Row():
                    search_btn = gr.Button("🔍 Search", variant="primary")
                    clear_btn = gr.Button("🗑️ Clear")
                    history_btn = gr.Button("📜 History")
            
            with gr.Column(scale=1):
                gr.Markdown("### 📝 Quick")
                dropdown = gr.Dropdown(choices=SUGGESTIONS, label="Search", interactive=True)
        
        output = gr.Textbox(label="🤖 Response", lines=18, interactive=False)
        
        # Quick buttons
        with gr.Row():
            btn1 = gr.Button("Analyze CVE-2024-6387", size="sm")
            btn2 = gr.Button("Fetch 5 CVEs", size="sm")
            btn3 = gr.Button("What is SQL injection?", size="sm")
            btn4 = gr.Button("Scan example.com", size="sm")
            btn5 = gr.Button("📜 History", size="sm")
            btn6 = gr.Button("🗑️ Clear", size="sm")
        
        def execute(q):
            return process_query(q)
        
        search_btn.click(execute, inputs=query, outputs=output)
        query.submit(execute, inputs=query, outputs=output)
        clear_btn.click(lambda: ("", ""), outputs=[query, output])
        history_btn.click(lambda: process_query("history"), outputs=output)
        dropdown.change(lambda x: x, inputs=dropdown, outputs=query)
        
        btn1.click(lambda: "analyze CVE-2024-6387", outputs=query)
        btn2.click(lambda: "fetch 5 cves", outputs=query)
        btn3.click(lambda: "What is SQL injection?", outputs=query)
        btn4.click(lambda: "scan https://example.com", outputs=query)
        btn5.click(lambda: "history", outputs=query)
        btn6.click(lambda: "clear", outputs=query)
        
        gr.Markdown("""
        ---
        ### 📊 About
        - 💾 All data saved locally in `./data/`
        - 📁 History stored in SQLite + JSON
        - 🔒 Fully offline (except NVD fetch)
        - 🚀 Model cached locally
        - 📱 Works on Mobile + Laptop
        """)
    
    return demo

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("\n🚀 Starting Bug Hunting AI - Offline Edition")
    print("=" * 50)
    print("💾 Data saved to: ./data/")
    print("📁 Model cached to: ./models/")
    print("=" * 50)
    
    demo = create_interface()
    demo.launch(
        server_name="0.0.0.0",  # All devices on same network
        server_port=7860,
        share=False,  # Fully local
        debug=False,
  )
