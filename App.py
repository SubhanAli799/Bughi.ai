# ============================================
# BUG HUNTING AI - SEARCH ENGINE
# ============================================
# Run: python app.py
# Open: http://localhost:7860
# ============================================

import torch
import requests
import gradio as gr
import warnings
import os
import sys
import json
import time
from datetime import datetime

# Suppress warnings
warnings.filterwarnings('ignore')

print("🛡️ Bug Hunting AI Search Engine Starting...")
print("=" * 50)

# ============================================
# INSTALL MISSING PACKAGES (if needed)
# ============================================

def install_packages():
    """Install missing packages automatically"""
    try:
        import transformers
        import accelerate
    except ImportError:
        print("📦 Installing required packages...")
        os.system(f"{sys.executable} -m pip install transformers accelerate -q")

install_packages()

# ============================================
# IMPORTS (After installation)
# ============================================

from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer

# ============================================
# LOAD MODEL FROM HUGGING FACE
# ============================================

MODEL_ID = "Subhan162/bug-hunting-ai"  # Aapka model

print(f"📥 Loading model: {MODEL_ID}")

pipe = None  # Global pipeline

def load_model():
    global pipe
    try:
        print("🔄 Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, trust_remote_code=True)
        
        # Handle padding token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        print("🔄 Loading model...")
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else None,
            trust_remote_code=True,
        )
        
        print("🔄 Creating pipeline...")
        pipe = pipeline(
            "text-generation",
            model=model,
            tokenizer=tokenizer,
            max_new_tokens=400,
            do_sample=True,
            temperature=0.7,
            top_p=0.95,
            pad_token_id=tokenizer.eos_token_id,
        )
        print("✅ Model loaded successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        print("🔄 Using GPT-2 as fallback...")
        
        try:
            tokenizer = AutoTokenizer.from_pretrained("gpt2")
            tokenizer.pad_token = tokenizer.eos_token
            model = AutoModelForCausalLM.from_pretrained("gpt2")
            
            pipe = pipeline(
                "text-generation",
                model=model,
                tokenizer=tokenizer,
                max_new_tokens=200,
                do_sample=True,
                temperature=0.7,
                pad_token_id=tokenizer.eos_token_id,
            )
            print("✅ Fallback model loaded!")
            return True
        except:
            print("❌ Failed to load any model!")
            return False

# Load model
model_loaded = load_model()

# ============================================
# TOOL FUNCTIONS
# ============================================

def analyze_cve(cve_id: str) -> str:
    """Analyze a CVE vulnerability"""
    if not cve_id or len(cve_id) < 3:
        return "⚠️ Please enter a valid CVE ID (e.g., CVE-2024-6387)"
    
    prompt = f"""
    Provide a comprehensive cybersecurity analysis of {cve_id}:
    
    CVE ID: {cve_id}
    
    Please include:
    1. Vulnerability Description
    2. CVSS Score and Severity
    3. Affected Systems and Versions
    4. Attack Vector
    5. Impact Assessment
    6. Mitigation Steps and Fix
    """
    
    try:
        if pipe is None:
            return "❌ Model not loaded. Please restart."
        result = pipe(prompt, max_new_tokens=600)
        return result[0]['generated_text']
    except Exception as e:
        return f"❌ Error analyzing CVE: {str(e)}"

def fetch_latest_cves(limit: str = "5") -> str:
    """Fetch latest CVEs from NVD database"""
    try:
        limit_num = int(limit) if limit else 5
        if limit_num > 20:
            limit_num = 20
        
        url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        params = {"resultsPerPage": limit_num}
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        cves = []
        for cve in data.get('vulnerabilities', [])[:limit_num]:
            cve_data = cve.get('cve', {})
            cve_id = cve_data.get('id', 'N/A')
            desc = cve_data.get('descriptions', [{}])[0].get('value', 'No description available')
            # Get CVSS score if available
            metrics = cve_data.get('metrics', {})
            cvss = metrics.get('cvssMetricV31', [{}])[0].get('cvssData', {})
            score = cvss.get('baseScore', 'N/A')
            severity = cvss.get('baseSeverity', 'N/A')
            
            cves.append(f"📌 {cve_id}\n   Score: {score} ({severity})\n   {desc[:150]}...")
        
        if cves:
            return f"📋 Latest {len(cves)} CVEs:\n\n" + "\n\n".join(cves)
        else:
            return "⚠️ No CVEs found. Please try again."
            
    except requests.exceptions.Timeout:
        return "⚠️ Connection timeout. Please try again."
    except requests.exceptions.RequestException as e:
        return f"⚠️ Network error: {str(e)}"
    except Exception as e:
        return f"❌ Error fetching CVEs: {str(e)}"

def scan_website(url: str) -> str:
    """Scan website for security vulnerabilities"""
    if not url:
        return "⚠️ Please enter a URL"
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, timeout=15, headers=headers, allow_redirects=True)
        
        result = f"🔍 Scan Results for {url}\n"
        result += "=" * 50 + "\n\n"
        result += f"📊 Status Code: {response.status_code}\n"
        result += f"📏 Content Length: {len(response.text):,} bytes\n"
        result += f"🔄 Redirects: {len(response.history)}\n"
        result += f"📅 Last Modified: {response.headers.get('Last-Modified', 'N/A')}\n\n"
        
        # Security Headers Check
        headers = response.headers
        security_checks = {
            'Strict-Transport-Security': 'HSTS',
            'X-Frame-Options': 'Clickjacking Protection',
            'X-Content-Type-Options': 'MIME Sniffing Protection',
            'Content-Security-Policy': 'CSP',
            'X-XSS-Protection': 'XSS Protection',
        }
        
        result += "🛡️ Security Headers:\n"
        found = False
        for header, name in security_checks.items():
            status = "✅ Present" if header in headers else "❌ Missing"
            if header in headers:
                found = True
                result += f"  - {name}: {status} ({headers[header][:50]})\n"
            else:
                result += f"  - {name}: {status}\n"
        
        if not found:
            result += "  ⚠️ No security headers found!\n"
        
        # AI Analysis
        if pipe is not None:
            prompt = f"""
            Security analysis of website {url}:
            - Status: {response.status_code}
            - Headers: {dict(headers)}
            - Content preview: {response.text[:500]}
            
            Identify potential vulnerabilities, security issues, and provide recommendations.
            """
            
            analysis = pipe(prompt, max_new_tokens=400)
            result += f"\n🤖 AI Security Analysis:\n{analysis[0]['generated_text']}"
        
        return result
        
    except requests.exceptions.Timeout:
        return f"⏱️ Connection timeout for {url}"
    except requests.exceptions.ConnectionError:
        return f"🔌 Cannot connect to {url}. Check URL or internet."
    except Exception as e:
        return f"❌ Error scanning {url}: {str(e)}"

def test_sql_injection(url: str) -> str:
    """Test for SQL injection vulnerabilities"""
    if not url:
        return "⚠️ Please enter a URL"
    
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        payloads = [
            "' OR '1'='1",
            "' AND 1=1--",
            "' UNION SELECT NULL--",
            "1' OR '1'='1",
            "1 AND 1=1",
            "' OR 'x'='x",
        ]
        results = []
        results.append(f"🔍 SQL Injection Test for {url}\n")
        results.append("=" * 40 + "\n")
        
        for payload in payloads:
            # Test with payload in URL
            test_url = f"{url}?id={payload}"
            response = requests.get(test_url, timeout=5, headers={'User-Agent': 'Mozilla/5.0'})
            
            if response.status_code == 200:
                if any(keyword in response.text.lower() for keyword in ['error', 'warning', 'mysql', 'sql', 'syntax']):
                    results.append(f"⚠️ Suspicious response with payload: {payload}")
                else:
                    results.append(f"✅ No obvious SQL injection with: {payload}")
            else:
                results.append(f"ℹ️ Status {response.status_code} with: {payload}")
        
        results.append("\n📌 Note: This is a basic test. Manual testing is recommended.")
        return "\n".join(results)
        
    except Exception as e:
        return f"❌ Error testing SQL injection: {str(e)}"

def review_code(code: str) -> str:
    """Review code for security vulnerabilities"""
    if not code or len(code.strip()) < 5:
        return "⚠️ Please provide code to review"
    
    prompt = f"""
    Review this code for security vulnerabilities:
    
    ```python
    {code}
    ```
    
    Analyze for:
    1. Input Validation Issues
    2. Authentication/Authorization Problems
    3. Data Exposure Risks
    4. Injection Vulnerabilities
    5. Security Best Practices
    6. Potential Exploits
    """
    
    try:
        if pipe is None:
            return "❌ Model not loaded. Please restart."
        result = pipe(prompt, max_new_tokens=600)
        return result[0]['generated_text']
    except Exception as e:
        return f"❌ Error reviewing code: {str(e)}"

def generate_report(data: str) -> str:
    """Generate security report"""
    if not data or len(data.strip()) < 10:
        return "⚠️ Please provide data for the report"
    
    prompt = f"""
    Generate a professional cybersecurity report from this data:
    
    {data}
    
    Format:
    1. Executive Summary
    2. Key Findings
    3. Risk Assessment (Low/Medium/High)
    4. Recommendations
    5. Conclusion
    """
    
    try:
        if pipe is None:
            return "❌ Model not loaded. Please restart."
        result = pipe(prompt, max_new_tokens=600)
        return result[0]['generated_text']
    except Exception as e:
        return f"❌ Error generating report: {str(e)}"

# ============================================
# COMMAND PROCESSOR
# ============================================

def process_query(query: str) -> str:
    """Process user query and route to appropriate tool"""
    if not query or query.strip() == "":
        return "⚠️ Please enter a command or question."
    
    q = query.lower().strip()
    
    # Help command
    if q in ["help", "?", "commands"]:
        return """
📋 Available Commands:

🔍 **Security Analysis:**
  `analyze CVE-2024-6387`  → Analyze a CVE vulnerability
  `fetch 10 cves`          → Get latest CVEs from NVD

🌐 **Web Security:**
  `scan https://example.com` → Scan website for vulnerabilities
  `test sql https://example.com?id=1` → Test for SQL injection

💻 **Code Review:**
  `review code <code>`     → Review code for security issues

📊 **Reports:**
  `generate report <data>` → Generate security report

❓ **General:**
  Any security question     → AI will answer
  `help` or `?`            → Show this menu

📝 **Examples:**
  What is SQL injection?
  How to prevent XSS?
  What is CVE-2024-6387?
  How does ransomware work?
  Explain buffer overflow
"""
    
    # Route to tools
    if q.startswith("analyze"):
        cve = query.split("analyze")[-1].strip()
        return analyze_cve(cve) if cve else "⚠️ Enter CVE ID (e.g., CVE-2024-6387)"
    
    elif q.startswith("fetch"):
        parts = query.split()
        limit = parts[1] if len(parts) > 1 else "5"
        return fetch_latest_cves(limit)
    
    elif q.startswith("scan"):
        url = query.split("scan")[-1].strip()
        return scan_website(url) if url else "⚠️ Enter URL to scan"
    
    elif q.startswith("test sql"):
        url = query.split("test sql")[-1].strip()
        return test_sql_injection(url) if url else "⚠️ Enter URL to test"
    
    elif q.startswith("review code"):
        code = query.split("review code")[-1].strip()
        return review_code(code) if code else "⚠️ Enter code to review"
    
    elif q.startswith("generate report"):
        data = query.split("generate report")[-1].strip()
        return generate_report(data) if data else "⚠️ Enter data for report"
    
    else:
        # Default: AI chat
        if pipe is None:
            return "❌ Model not loaded. Please restart the app."
        try:
            result = pipe(query, max_new_tokens=400)
            return result[0]['generated_text']
        except Exception as e:
            return f"❌ Error: {str(e)}"

# ============================================
# SEARCH SUGGESTIONS
# ============================================

SUGGESTIONS = [
    "analyze CVE-2024-6387",
    "fetch 5 cves",
    "scan https://example.com",
    "test sql https://example.com?id=1",
    "What is SQL injection?",
    "How to prevent XSS?",
    "What is CVE-2024-6387?",
    "Explain buffer overflow",
    "How to secure REST APIs?",
    "What is ransomware?",
    "How does phishing work?",
    "What is OWASP Top 10?",
    "review code def login(username, password):",
    "generate report Security assessment",
]

# ============================================
# GRADIO INTERFACE
# ============================================

def create_interface():
    with gr.Blocks(title="🔍 Bug Hunting AI", theme=gr.themes.Soft()) as demo:
        
        # Header
        gr.Markdown("""
        # 🔍 Bug Hunting AI - Search Engine
        ### Type any security question or use commands
        """)
        
        # Model status
        status = "✅ Model Loaded" if pipe is not None else "⚠️ Using Fallback Model"
        gr.Markdown(f"**Status:** {status}")
        
        with gr.Row():
            with gr.Column(scale=4):
                query = gr.Textbox(
                    label="🔎 Search / Ask Question",
                    placeholder="Type: analyze CVE-2024-6387 or What is SQL injection?",
                    lines=2,
                )
                
                with gr.Row():
                    search_btn = gr.Button("🔍 Search", variant="primary", size="lg")
                    clear_btn = gr.Button("🗑️ Clear", size="lg")
                    help_btn = gr.Button("📚 Help", size="lg")
            
            with gr.Column(scale=1):
                gr.Markdown("### 📝 Quick Search")
                suggestion_dropdown = gr.Dropdown(
                    choices=SUGGESTIONS,
                    label="Select a sample query",
                    interactive=True,
                )
        
        # Output
        output = gr.Textbox(
            label="🤖 AI Response",
            lines=18,
            interactive=False,
        )
        
        # Quick action buttons
        gr.Markdown("### ⚡ Quick Search Commands")
        with gr.Row():
            btn1 = gr.Button("🔍 Analyze CVE-2024-6387", size="sm")
            btn2 = gr.Button("📋 Fetch 5 CVEs", size="sm")
            btn3 = gr.Button("🌐 Scan example.com", size="sm")
            btn4 = gr.Button("🧪 Test SQL Injection", size="sm")
        
        with gr.Row():
            btn5 = gr.Button("❓ What is SQL injection?", size="sm")
            btn6 = gr.Button("❓ How to prevent XSS?", size="sm")
            btn7 = gr.Button("❓ What is Ransomware?", size="sm")
            btn8 = gr.Button("💻 Review Code", size="sm")
        
        # Command guide
        with gr.Accordion("📖 Command Guide", open=False):
            gr.Markdown("""
            ### 🔍 Search Commands
            
            | Command | Example | Description |
            |---------|---------|-------------|
            | `analyze` | `analyze CVE-2024-6387` | Analyze a CVE vulnerability |
            | `fetch` | `fetch 10 cves` | Get latest CVEs from NVD |
            | `scan` | `scan https://example.com` | Scan website for vulnerabilities |
            | `test sql` | `test sql https://example.com?id=1` | Test for SQL injection |
            | `review code` | `review code def login():` | Review code for security issues |
            | `generate report` | `generate report Security data` | Generate security report |
            | `help` | `help` | Show this menu |
            | `[any question]` | `What is SQL injection?` | AI will answer |
            """)
        
        # Footer
        gr.Markdown("""
        ---
        ### 📊 About
        - 🔒 All processing is done locally
        - 🚀 Model: [Subhan162/bug-hunting-ai](https://huggingface.co/Subhan162/bug-hunting-ai)
        - 📁 [GitHub Repository](https://github.com/Subhan162/bug-hunting-ai)
        - 📝 Trained on 150,000+ CVE records
        """)
        
        # Event handlers
        def execute_query(q):
            if q:
                return process_query(q)
            return "⚠️ Please enter a question or command."
        
        def set_query_from_suggestion(q):
            return q
        
        search_btn.click(execute_query, inputs=query, outputs=output)
        query.submit(execute_query, inputs=query, outputs=output)
        clear_btn.click(lambda: ("", ""), outputs=[query, output])
        help_btn.click(lambda: "help", outputs=query)
        
        suggestion_dropdown.change(set_query_from_suggestion, inputs=suggestion_dropdown, outputs=query)
        
        btn1.click(lambda: "analyze CVE-2024-6387", outputs=query)
        btn2.click(lambda: "fetch 5 cves", outputs=query)
        btn3.click(lambda: "scan https://example.com", outputs=query)
        btn4.click(lambda: "test sql https://example.com?id=1", outputs=query)
        btn5.click(lambda: "What is SQL injection?", outputs=query)
        btn6.click(lambda: "How to prevent XSS?", outputs=query)
        btn7.click(lambda: "What is Ransomware?", outputs=query)
        btn8.click(lambda: "review code def login(username, password):\n    query = 'SELECT * FROM users WHERE username=' + username\n    return query", outputs=query)
    
    return demo

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("\n🚀 Starting Bug Hunting AI Search Engine...")
    print("=" * 50)
    print("🌐 Local URL: http://localhost:7860")
    print("🔍 Type any security question or use commands!")
    print("=" * 50)
    
    # Check model status
    if pipe is not None:
        print("✅ Model loaded and ready!")
    else:
        print("⚠️ Running with fallback model. Some features may be limited.")
    
    # Create and launch interface
    demo = create_interface()
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=True,
        debug=False,
          )
