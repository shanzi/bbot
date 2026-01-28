---
name: pdf-processing
description: Advanced PDF operations including text extraction, cropping, thumbnail generation, and preview creation. Handles PDF manipulation and visual representation for user feedback.
---

# PDF Processing

Specialized tools for working with PDF documents, including extraction, manipulation, and preview generation.

## Available Operations

### 1. Text Extraction

Extract text content from PDF files for analysis and summarization.

**Usage:**
- Use `pdf_to_text` tool with appropriate `truncate_limit_tokens` parameter
- For summaries: Use small limit (e.g., 200 tokens) to get overview
- For full text: Increase limit or omit for complete extraction

**Best Practice:**
- Extract efficiently to avoid token waste
- Use extracted text for content-based naming
- Generate markdown summaries from extracted text

### 2. PDF Cropping

Crop PDF margins to improve readability and reduce file size.

**Process:**
1. Identify PDF that needs margin trimming
2. Use appropriate cropping tool
3. Save cropped file to `data/document/cropped/` folder
4. Use the same content-based name as original
5. Apply ASCII-safe naming rules (no parentheses, brackets, or special characters)

**Example:**
- Original: `data/document/Research-Paper-2024.pdf`
- Cropped: `data/document/cropped/Research-Paper-2024.pdf`

### 3. Thumbnail Generation

Generate visual previews of PDF documents for user feedback.

**When to Create Thumbnails:**
- User requests PDF preview
- After sending document to Kindle (notification)
- When displaying document in conversation

**Thumbnail Specifications:**
- Generate medium-sized thumbnail of first page
- Save to `data/document/thumbnail/` folder
- **CRITICAL**: Use ASCII-safe filenames with NO parentheses or brackets
- Replace spaces with hyphens or underscores
- Same base name as document with appropriate extension

**Example:**
- Document: `Machine-Learning-Healthcare-2024.pdf`
- Thumbnail: `data/document/thumbnail/Machine-Learning-Healthcare-2024.jpg`

### 4. Preview Display

Show PDF previews to users using Markdown image syntax.

**Format:**
```markdown
![PDF Preview](data/document/thumbnail/filename.jpg)
```

**Requirements:**
- Path must start from 'data' directory
- Filename must use only ASCII characters
- No parentheses, brackets, or special characters
- Use hyphens or underscores instead of spaces

### 5. PDF to Image Conversion

Convert PDF pages to images for visual display or processing.

**Use Cases:**
- Create previews for Telegram
- Generate thumbnails for document catalog
- Extract specific pages as images

**Output:**
- Save to appropriate folder based on purpose
- Thumbnail folder for previews
- Pictures folder for extracted pages
- Always use ASCII-safe naming

## Naming Rules for PDF Files

All PDF-related files must follow strict ASCII-safe naming:

### ✅ Allowed Characters
- Letters: a-z, A-Z
- Numbers: 0-9
- Hyphens: `-`
- Underscores: `_`
- Dots: `.` (for extensions)

### ❌ Forbidden Characters
- Parentheses: `()` - Break markdown parsing
- Brackets: `[]` - Break path resolution
- Spaces: ` ` - Use hyphens or underscores instead
- Special characters: `éñü@#$%&*` - Cause encoding issues

### Conversion Examples
- `Report (2024).pdf` → `Report-2024.pdf`
- `[Draft] Document.pdf` → `Draft-Document.pdf`
- `Résumé François.pdf` → `Resume-Francois.pdf`
- `File #1 & Notes.pdf` → `File-1-and-Notes.pdf`

## Workflow Examples

### Example 1: Preview PDF
```
1. User asks: "Preview the research paper"
2. Generate thumbnail: pdf_to_image(first_page=True)
3. Save to: data/document/thumbnail/Research-Paper-2024.jpg
4. Display: ![Preview](data/document/thumbnail/Research-Paper-2024.jpg)
```

### Example 2: Crop PDF Margins
```
1. User asks: "Trim margins on the document"
2. Crop PDF using appropriate tool
3. Save to: data/document/cropped/Document-Name.pdf
4. Notify user of location
```

### Example 3: Extract and Summarize
```
1. Extract text with truncate_limit_tokens=200
2. Analyze content for key topics
3. Create markdown summary
4. Save as: data/document/Document-Name.md
```

## Integration with Document Management

PDF processing works seamlessly with document management:

1. **After Download**: Extract text → Analyze → Rename based on content
2. **After Rename**: Generate thumbnail → Create summary
3. **For Kindle**: Send document → Generate thumbnail → Show confirmation
4. **For Preview**: Create thumbnail → Display with Markdown

## Best Practices

1. Always generate thumbnails with ASCII-safe names
2. Use consistent naming between document and related files
3. Save cropped PDFs to dedicated cropped folder
4. Generate thumbnails before sending Kindle notifications
5. Extract text efficiently using token limits
6. Maintain file organization across all PDF operations
7. Test image paths work with Markdown syntax
