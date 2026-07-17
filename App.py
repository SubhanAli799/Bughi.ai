
---

## 📄 File 2: app.py (Main Web App)

```python
# ============================================
# BUG HUNTING AI - LOCAL WEB APP
# ============================================
# Save as: app.py
# Run: python app.py
# Open: http://localhost:8000
# ============================================

import gradio as gr
from transformers import pipeline
import torch
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("🛡️ Starting Bug Hunting AI...")
print("=" * 50)

# ============================================
# CONFIGURATION
# ============================================

# Option 1: From Hugging Face (Recommended)
MODEL_ID = os.getenv("MODEL_ID", "Subhan162/bug-hunting-ai")

# Option 2: From local folder
LOCAL_MODEL_PATH = os.getenv("LOCAL_MODEL_PATH", "./model")

# Use local model if exists, else use Hugging Face
if os.path.exists(LOCAL_MODEL_PATH):
    MODEL_ID = LOCAL_MODEL_PATH
    print(f"📁 Using local model: {MODEL_ID}")
else:
    print(f"📥 Using Hugging Face model: {MODEL_ID}")

# ============================================
# LOAD MODEL
# ============================================

print("\n📥 Loading model...")
print("⏳ This may take a few minutes...")

try:
    # Use GPU if available
    device = 0 if torch.cuda.is_available() else -1
    print(f"💻 Using device: {'GPU' if device == 0 else 'CPU'}")
    
    pipe = pipeline(
        "text-generation",
        model=MODEL_ID,
        device_map="auto" if torch.cuda.is_available() else None,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        trust_remote_code=True,
    )
    
    print("✅ Model loaded successfully!")
    
except Exception as e:
    print(f"❌ Error loading model: {e}")
    print("\n💡 Try:")
    print("1. Check internet connection")
    print("2. Verify MODEL_ID is correct")
    print("3. Use local model: set LOCAL_MODEL_PATH")
    exit(1)

# ============================================
# CHAT FUNCTION
# ============================================

def chat(question, max_tokens=300, temperature=0.7):
    """
    Generate response for bug hunting questions
    """
    if not question or question.strip() == "":
        return "⚠️ Please enter a question."
    
    try:
        # Generate response
        result = pipe(
            question,
            max_new_tokens=max_tokens,
            do_sample=True,
            temperature=temperature,
            top_p=0.95,
            pad_token_id=50256,  # GPT-2 specific
        )
        
        # Extract response
        response = result[0]['generated_text']
        
        # Clean up response if needed
        if "Answer:" in response:
            response = response.split("Answer:")[-1].strip()
        elif "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()
        
        return response
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

# ============================================
# SAMPLE QUESTIONS
# ============================================

SAMPLE_QUESTIONS = [
    "Analyze CVE-2024-6387 vulnerability",
    "What is SQL injection and how to prevent it?",
    "Explain buffer overflow attack with example",
    "How to secure REST APIs from attacks?",
    "What is Cross-Site Scripting (XSS)?",
    "Explain Log4Shell vulnerability",
    "How to prevent privilege escalation?",
]

# ============================================
# GRADIO UI
# ============================================

def create_interface():
    with gr.Blocks(title="🛡️ Bug Hunting AI", theme=gr.themes.Soft()) as demo:
        
        # Header
        gr.Markdown("""
        # 🛡️ Bug Hunting AI
        ### Ask any question about CVEs, vulnerabilities, or cybersecurity!
        """)
        
        with gr.Row():
            with gr.Column(scale=2):
                # Input
                question = gr.Textbox(
                    label="💬 Ask about vulnerabilities",
                    placeholder="e.g., What is CVE-2024-6387?",
                    lines=3,
                )
                
                with gr.Row():
                    submit_btn = gr.Button("🔍 Analyze", variant="primary")
                    clear_btn = gr.Button("🗑️ Clear")
                
                # Advanced options
                with gr.Accordion("⚙️ Advanced Settings", open=False):
                    max_tokens = gr.Slider(
                        minimum=50,
                        maximum=500,
                        value=300,
                        step=50,
                        label="Max Response Length (tokens)",
                    )
                    temperature = gr.Slider(
                        minimum=0.1,
                        maximum=1.5,
                        value=0.7,
                        step=0.1,
                        label="Temperature (Creativity)",
                    )
            
            with gr.Column(scale=3):
                # Output
                output = gr.Textbox(
                    label="🤖 AI Response",
                    lines=15,
                    interactive=False,
                )
        
        # Sample questions
        gr.Markdown("### 📝 Sample Questions")
        sample_btns = []
        for q in SAMPLE_QUESTIONS:
            btn = gr.Button(q, size="sm")
            sample_btns.append(btn)
            btn.click(fn=lambda x=q: x, outputs=question)
        
        # Event handlers
        submit_btn.click(
            fn=chat,
            inputs=[question, max_tokens, temperature],
            outputs=output,
        )
        
        question.submit(
            fn=chat,
            inputs=[question, max_tokens, temperature],
            outputs=output,
        )
        
        clear_btn.click(
            fn=lambda: ("", ""),
            outputs=[question, output],
        )
        
        # Footer
        gr.Markdown("""
        ---
        ### 📌 Notes
        - 🔒 All processing is done locally on your machine
        - 🚀 Model trained on 150,000+ CVE records
        - ⚡ Responses may take a few seconds
        - 💡 Use this as a reference, not as authoritative security advice
        - 📊 [Model Details](https://huggingface.co/Subhan162/bug-hunting-ai)
        """)
    
    return demo

# ============================================
# MAIN
# ============================================

if __name__ == "__main__":
    print("\n🚀 Starting Bug Hunting AI Web App...")
    print("=" * 50)
    print("🌐 Local URL: http://localhost:8000")
    print("📝 Ask questions about CVEs and vulnerabilities!")
    print("=" * 50)
    
    # Create and launch app
    demo = create_interface()
    demo.launch(
        server_name="127.0.0.1",
        server_port=8000,
        share=True,  # Creates a public link
        debug=False,
)
