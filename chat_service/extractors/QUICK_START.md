# Quick Start: Enhanced Content Extraction

## 5-Minute Setup

### 1. Install Dependencies (2 minutes)

```bash
cd chat_service
pip install -r requirements.txt
playwright install chromium
```

### 2. Test It Works (1 minute)

```bash
python test_enhanced_extraction.py
```

You should see successful extractions from multiple URLs!

### 3. Use in Your Code (2 minutes)

```python
from extractors import ExtractionOrchestrator

# Create orchestrator (do this once)
orchestrator = ExtractionOrchestrator(use_cache=True)

# Extract content (use many times)
result = await orchestrator.extract_url("https://example.com")

print(result['title'])
print(result['content'])
```

That's it! You're extracting content with free tools.

---

## Common Use Cases

### Extract Article Content

```python
result = await orchestrator.extract_url(
    url="https://medium.com/article",
    format="markdown"
)
```

### Extract GitHub README

```python
result = await orchestrator.extract_url(
    url="https://github.com/user/repo",
    method="github"
)
```

### Extract Documentation

```python
result = await orchestrator.extract_url(
    url="https://docs.python.org/3/",
    format="html"
)
```

---

## What You Get

Every extraction returns:

```python
{
    "title": "Page Title",
    "content": "Clean extracted content",
    "text": "Plain text version",
    "html": "Clean HTML version",
    "author": "Author name (if available)",
    "date": "Publication date (if available)",
    "images": ["image1.jpg", "image2.jpg"],
    "metadata": {"url": "...", "sitename": "..."},
    "extraction_method": "trafilatura",
    "extraction_time": 1.23,
    "success": True,
    "cached": False
}
```

---

## Tips

1. **Use caching** - Set `use_cache=True` (default)
2. **Check success** - Always check `result['success']`
3. **Handle errors** - Wrap in try/except
4. **Monitor stats** - Call `orchestrator.get_stats()`
5. **Clear cache** - Call `orchestrator.clear_cache()` if needed

---

## Need Help?

- Read: `INSTALL_ENHANCED_EXTRACTION.md` (full guide)
- Test: `python test_enhanced_extraction.py <url>`
- Check logs: Look for extraction errors

---

## Why This is Better Than Paid APIs

| Feature | Our Solution | Jina/Firecrawl |
|---------|--------------|----------------|
| Cost | FREE | $49/month |
| Rate Limits | NONE | 100-500/day |
| Speed | 1-3s | 1-2s |
| Privacy | Local | Cloud |
| Control | Full | None |

**You made the right choice!** 🎉
