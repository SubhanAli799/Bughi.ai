# tests/test_model.py
import pytest
from transformers import pipeline

def test_model_load():
    """Test that model loads successfully"""
    try:
        pipe = pipeline("text-generation", model="Subhan162/bug-hunting-ai")
        assert pipe is not None
    except Exception as e:
        pytest.fail(f"Model failed to load: {e}")

def test_model_response():
    """Test that model generates response"""
    pipe = pipeline("text-generation", model="Subhan162/bug-hunting-ai")
    result = pipe("Test question", max_new_tokens=50)
    assert len(result) > 0
    assert 'generated_text' in result[0]
