from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="bug-hunting-ai",
    version="1.0.0",
    author="Subhan162",
    author_email="your_email@example.com",
    description="AI model for cybersecurity vulnerability analysis and bug hunting",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Subhan162/bug-hunting-ai",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Security",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
    ],
    python_requires=">=3.8",
    install_requires=[
        "transformers>=4.30.0",
        "torch>=2.0.0",
        "gradio>=4.0.0",
        "accelerate>=0.20.0",
        "huggingface_hub>=0.20.0",
        "python-dotenv>=1.0.0",
    ],
)
