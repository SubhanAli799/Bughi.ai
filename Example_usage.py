# examples/example_usage.py
from transformers import pipeline

def main():
    # Load model
    print("Loading model...")
    pipe = pipeline("text-generation", model="Subhan162/bug-hunting-ai")
    
    # Test questions
    questions = [
        "Analyze CVE-2024-6387:",
        "What is SQL injection?",
        "Explain buffer overflow attack:",
    ]
    
    for q in questions:
        print(f"\n📝 Question: {q}")
        result = pipe(q, max_new_tokens=150, do_sample=True, temperature=0.7)
        print(f"🤖 {result[0]['generated_text']}")
        print("-" * 50)

if __name__ == "__main__":
    main()
