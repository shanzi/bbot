---
name: web-content
description: Fetch and process web content. Download files from URLs, convert webpages to PDF, and handle various web-based content types with intelligent classification.
---

# Web Content Processing

Handle web-based content including URL fetching, file downloads, and webpage to PDF conversion.

## URL Classification

When a user provides a URL, determine the content type:

### Direct Document Links
URLs pointing directly to files (PDF, DOC, DOCX, EPUB, etc.)

**Indicators:**
- Ends with file extension: `.pdf`, `.doc`, `.docx`, `.epub`, `.zip`
- MIME type indicates document
- Direct download link

**Examples:**
```
https://example.com/paper.pdf
https://domain.com/download/book.epub
https://site.org/files/document.docx
```

**Action:** Use `download_file` tool to save directly

### Webpage URLs
URLs pointing to HTML pages, blog posts, articles, etc.

**Indicators:**
- No file extension or ends with `.html`, `.htm`
- Contains webpage content
- Needs rendering/parsing

**Examples:**
```
https://blog.example.com/article
https://wikipedia.org/wiki/Topic
https://docs.site.com/guide.html
```

**Action:** Fetch and summarize first, then convert to PDF if requested

## Operations

### 1. Download Files from URLs

Download documents directly from web URLs.

**Tool:** `download_file`

**Process:**
1. Identify URL points to a document
2. Use download_file tool
3. Save to 'data/document' folder
4. Tool automatically detects filename from URL or uses generic name
5. Follow content-based renaming procedure
6. Generate summary

**Example:**
```
User: "Download https://arxiv.org/pdf/2301.00001.pdf"

1. download_file("https://arxiv.org/pdf/2301.00001.pdf")
2. Saved to: data/document/2301.00001.pdf
3. Extract text with pdf_to_text
4. Analyze content: "Transformer Architecture for NLP"
5. Rename to: data/document/Transformer-Architecture-NLP-2023.pdf
6. Create summary: data/document/Transformer-Architecture-NLP-2023.md
7. Confirm with user
```

### 2. Fetch and Summarize Webpages

Retrieve webpage content and provide summary.

**Tool:** `fetch` or web fetching capability

**Process:**
1. Fetch webpage content
2. Extract main text (remove navigation, ads, etc.)
3. Summarize key points
4. Present to user
5. Ask if they want to save as PDF

**Example:**
```
User: "What's on https://blog.example.com/ai-trends"

1. Fetch webpage content
2. Extract article text
3. Summarize: "Article discusses 5 AI trends in 2026:
   - Multimodal models
   - Edge AI deployment
   - ..."
4. Ask: "Would you like me to save this as a PDF?"
```

### 3. Convert Webpage to PDF

Save webpage as PDF document in library.

**Tool:** `webpage_to_pdf`

**Parameters:**
- `url` - Webpage URL
- `output_path` - Optional output location (defaults to data/document/)
- `filename` - Optional filename (generated from page title if not provided)

**Process:**
1. User requests to save webpage or you offer after summarizing
2. Use webpage_to_pdf tool
3. Tool extracts page title for filename
4. Converts to PDF with proper formatting
5. Saves to data/document/
6. Apply ASCII-safe naming rules
7. Generate thumbnail for preview

**Example:**
```
User: "Save that article as PDF"

1. webpage_to_pdf("https://blog.example.com/ai-trends")
2. Extracts title: "Top AI Trends for 2026"
3. Generates filename: "Top-AI-Trends-for-2026.pdf"
4. Saves to: data/document/Top-AI-Trends-for-2026.pdf
5. Generate thumbnail for preview
6. Display thumbnail
7. Confirm: "Saved as 'Top-AI-Trends-for-2026.pdf'"
```

## Workflow Patterns

### Pattern 1: Direct PDF Download
```
User: "Download this paper: https://arxiv.org/pdf/2301.12345.pdf"

1. Identify: Direct PDF link
2. download_file("https://arxiv.org/pdf/2301.12345.pdf")
3. Initial save: data/document/2301.12345.pdf
4. Extract text and analyze content
5. Rename based on content: "Neural-Networks-Survey-2023.pdf"
6. Create markdown summary
7. Confirm: "Downloaded and saved as 'Neural-Networks-Survey-2023.pdf'"
```

### Pattern 2: Webpage Summary then Save
```
User: "Check out https://techblog.com/new-framework"

1. Identify: Webpage URL
2. Fetch and parse content
3. Summarize for user: "Article about new JavaScript framework 'FastJS'..."
4. User: "Save it"
5. webpage_to_pdf("https://techblog.com/new-framework")
6. Save as: data/document/FastJS-New-Framework.pdf
7. Generate thumbnail
8. Display: ![Preview](data/document/thumbnail/FastJS-New-Framework.jpg)
```

### Pattern 3: Ambiguous URL
```
User: "Get https://example.com/docs/guide"

1. Attempt to determine type
2. If unclear, fetch first
3. Check Content-Type header
4. If HTML: Summarize, offer to save as PDF
5. If document: Download directly
6. Follow appropriate workflow
```

### Pattern 4: Multiple URLs
```
User: "Download these papers: [url1], [url2], [url3]"

1. Process each URL sequentially
2. For each:
   - Download file
   - Rename based on content
   - Create summary
3. Provide summary of all downloaded files
4. List final filenames and locations
```

## File Naming from URLs

Extract meaningful names from URLs:

### Good URL Patterns
```
https://example.com/paper-name.pdf → paper-name.pdf
https://domain.com/files/2024-report.pdf → 2024-report.pdf
https://site.org/download?file=book.epub → book.epub
```

### Generic URL Patterns
```
https://example.com/download?id=12345 → Use content analysis
https://api.site.com/file/abc123 → Extract text and create name
```

### Apply Content-Based Naming
1. Download with generic name
2. Extract content (text for PDFs, title for webpages)
3. Analyze and create descriptive name
4. Rename following ASCII-safe rules
5. No parentheses, brackets, or special characters

## URL Validation

Before processing URLs:

1. **Check format:** Valid HTTP/HTTPS URL
2. **Check accessibility:** URL responds (not 404)
3. **Check size:** Warn if very large file
4. **Check type:** Appropriate content type
5. **Handle errors:** Inform user if URL invalid

**Error Handling:**
```
- 404 Not Found → "URL not accessible"
- 403 Forbidden → "Access denied to resource"
- Connection timeout → "Unable to reach URL"
- Too large → "File is X GB, proceed? (y/n)"
```

## Content Extraction

### From PDFs
- Use `pdf_to_text` with token limit
- Extract title, authors, abstract
- Identify document type (paper, report, book)

### From Webpages
- Extract `<title>` tag
- Find main content (article, blog post)
- Remove navigation, ads, footers
- Preserve formatting where possible

### From Other Documents
- DOCX: Extract text and metadata
- EPUB: Extract title and author
- HTML: Parse and extract text
- Text files: Read directly

## Integration with Document Management

Web content processing integrates seamlessly:

1. **Download** → data/document/
2. **Extract** → Analyze content
3. **Rename** → Content-based naming
4. **Summarize** → Create .md file
5. **Organize** → Proper directory structure
6. **Preview** → Generate thumbnails

## Best Practices

1. **Always classify URL first** - Direct download vs webpage
2. **Summarize before saving webpages** - User may not want PDF
3. **Use content-based naming** - Don't keep generic names
4. **Apply ASCII-safe naming rules** - Prevent path issues
5. **Generate thumbnails for saved webpages** - Visual confirmation
6. **Check file size before downloading** - Warn about large files
7. **Validate URLs** - Handle errors gracefully
8. **Create summaries** - Make content searchable
9. **Respect content structure** - Preserve formatting in PDFs
10. **Clean up temp files** - Remove intermediate files

## Common Use Cases

### Research Paper Collection
```
User provides list of arxiv URLs
1. Download each PDF
2. Extract title, authors, year
3. Rename: "Title-Authors-Year.pdf"
4. Create summaries
5. Organize by topic
```

### Article Archive
```
User wants to save blog posts
1. For each URL:
   - Fetch and summarize
   - Convert to PDF
   - Extract title for filename
   - Generate preview thumbnail
2. Create collection in data/document/
```

### Documentation Backup
```
User wants offline copies of docs
1. Identify documentation URLs
2. Convert to PDFs
3. Organize by topic
4. Create index/summary
```

## Advanced Features

### Batch Processing
Handle multiple URLs efficiently:
1. Process in sequence (avoid overwhelming)
2. Progress updates per URL
3. Summary at end
4. Error handling per URL

### Smart Classification
Improve URL classification:
- Check file extensions
- Inspect MIME types
- Analyze URL patterns
- Use HEAD request to check before downloading

### Content Optimization
Optimize saved content:
- Compress large PDFs
- Remove unnecessary pages
- Optimize images in PDFs
- Clean up HTML formatting

## Security Considerations

1. **Validate URLs** - Check for malicious links
2. **Limit file sizes** - Prevent disk filling
3. **Scan downloads** - Check for malware if possible
4. **Respect robots.txt** - Don't scrape restricted content
5. **Handle credentials** - Never log or expose API keys
6. **Rate limiting** - Don't overwhelm servers
7. **Privacy** - Don't log user's browsing URLs

## Error Recovery

Handle common failures gracefully:

| Error | Recovery |
|-------|----------|
| URL unreachable | Retry once, then inform user |
| File too large | Ask user to confirm before downloading |
| Invalid format | Suggest alternatives or manual download |
| Conversion failed | Save original, explain limitation |
| Network timeout | Retry with longer timeout |
