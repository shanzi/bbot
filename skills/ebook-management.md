---
name: ebook-management
description: Manage ebook library with Calibre integration. Add books, convert formats (PDF/EPUB/MOBI), search library, and send books directly to Kindle. Full ebook lifecycle management.
---

# Ebook Management with Calibre

Comprehensive ebook library management through Calibre integration via the `calibre` MCP server.

## Available Operations

### 1. Add Ebooks to Library

Import ebooks into the Calibre library.

**Tool:** `add_ebook`

**Parameters:**
- `file_path` - Path to ebook file (required)
- `title` - Book title (optional, auto-detected if not provided)
- `authors` - Book authors (optional, auto-detected if not provided)

**Supported Formats:**
- PDF, EPUB, MOBI, AZW3
- TXT, HTML, RTF
- DOCX and other document formats

**Process:**
1. User uploads ebook or provides path
2. Add to Calibre library with `add_ebook`
3. Metadata is automatically extracted
4. Book gets unique ID in library
5. Confirm addition with user

**Example:**
```
User uploads: "Machine Learning Guide.epub"
1. Save to data/attachment/
2. add_ebook(file_path="/path/to/file.epub")
3. Calibre extracts title, author, metadata
4. Confirm: "Added 'Machine Learning Guide' by John Smith to library (ID: 123)"
```

### 2. List Ebooks

Browse and search the ebook library.

**Tool:** `list_ebooks`

**Parameters:**
- `search` - Optional search query
- Supports partial title matches
- Searches authors and titles

**Use Cases:**
- User: "Show me all books" → list_ebooks()
- User: "Find Python books" → list_ebooks(search="Python")
- User: "Books by Smith" → list_ebooks(search="Smith")

**Display Format:**
- Show book ID, title, authors
- Indicate available formats
- Show file sizes if relevant

### 3. Search Books (Advanced)

Perform advanced searches with filters.

**Tool:** `search_books`

**Search Syntax:**
- `author:Smith` - Books by specific author
- `title:Learning` - Books with "Learning" in title
- `tag:programming` - Books tagged as programming
- Can combine multiple filters

**Examples:**
```
search_books("author:Knuth tag:algorithms")
search_books("title:Python author:Van Rossum")
search_books("tag:fiction published:2024")
```

### 4. Get Book Details

Retrieve comprehensive information about a book.

**Tool:** `get_book_info`

**Parameters:**
- `book_id` - Calibre book identifier

**Returns:**
- Complete metadata (title, authors, publisher, ISBN)
- Available formats
- File paths
- Tags and series information
- Date added, last modified
- Cover image path

**Use When:**
- User asks for book details
- Before converting or exporting
- Displaying book information

### 5. Convert Ebook Formats

Convert books between different formats.

**Tool:** `convert_ebook`

**Parameters:**
- `book_id` - Source book identifier
- `output_format` - Target format (e.g., "MOBI", "EPUB", "PDF")

**Common Conversions:**
- EPUB → MOBI (for Kindle)
- PDF → EPUB (for e-readers)
- MOBI → PDF (for reading/sharing)
- Any format → AZW3 (modern Kindle)

**Process:**
1. Identify source book and current format
2. Determine target format needed
3. Run conversion with convert_ebook
4. Verify conversion successful
5. Inform user of new format availability

**Example:**
```
User: "Convert the Python book to MOBI for my Kindle"
1. search_books("title:Python") → Get book_id
2. convert_ebook(book_id=123, output_format="MOBI")
3. Confirm: "Converted to MOBI format, ready for Kindle"
```

### 6. Export Books

Export books from library to specified location.

**Tool:** `export_book`

**Parameters:**
- `book_id` - Book to export
- `output_directory` - Destination path
- `format` - Optional specific format (uses best available if not specified)

**Use Cases:**
- Export to data/document/ for sharing
- Copy to external drive
- Backup specific books
- Prepare for manual transfer

**Example:**
```
export_book(book_id=123, output_directory="data/document/", format="EPUB")
```

### 7. Send to Kindle

Send books directly to Kindle device via email.

**Tool:** `send_book_to_kindle`

**Parameters:**
- `book_id` - Book to send
- `format` - Preferred format ("MOBI", "AZW3", or "PDF")

**Process:**
1. Find book in library
2. Convert to Kindle-compatible format if needed
3. Export book temporarily
4. Email to Kindle address (from GMAIL_ADDRESS to KINDLE_ADDRESS)
5. Clean up temporary files
6. Generate thumbnail for confirmation
7. Show thumbnail to user as notification

**Kindle Format Preferences:**
- **MOBI** - Compatible with all Kindles, good for text
- **AZW3** - Modern format, better formatting, Kindle Paperwhite and newer
- **PDF** - Last resort, preserves layout but less readable

**Example:**
```
User: "Send the Python book to my Kindle"
1. search_books("title:Python") → book_id=123
2. send_book_to_kindle(book_id=123, format="MOBI")
3. Generate thumbnail of first page
4. Display: ![Sent to Kindle](data/document/thumbnail/Python-Book.jpg)
5. Confirm: "Sent to your Kindle! Check your device in a few minutes."
```

## Environment Configuration

Required environment variables (from `.env`):

- `CALIBRE_LIBRARY_PATH` - Path to Calibre library (default: ~/Calibre Library)
- `GMAIL_ADDRESS` - Gmail address for sending to Kindle
- `GMAIL_APP_PASSWORD` - Gmail app password
- `KINDLE_ADDRESS` - Kindle email address (e.g., username@kindle.com)

## Library Structure

Calibre organizes books as:
```
Calibre Library/
├── Author Name/
│   └── Book Title (ID)/
│       ├── cover.jpg
│       ├── metadata.opf
│       └── Book Title.epub
```

The library is also accessible via the `filesystem` MCP server for direct file operations.

## Workflow Examples

### Example 1: Add and Organize New Book
```
1. User uploads "ml-guide.pdf"
2. add_ebook(file_path="data/attachment/ml-guide.pdf")
3. Calibre extracts metadata → "Machine Learning Guide by John Smith"
4. Book added with ID 456
5. Confirm: "Added to library as 'Machine Learning Guide' (ID: 456)"
```

### Example 2: Find and Convert Book
```
User: "Convert my React book to MOBI"

1. search_books("title:React") → Found book ID 789
2. get_book_info(book_id=789) → Currently EPUB format
3. convert_ebook(book_id=789, output_format="MOBI")
4. Confirm: "Converted 'Learning React' to MOBI format"
```

### Example 3: Send to Kindle with Notification
```
User: "Send the algorithm book to Kindle"

1. search_books("tag:algorithms") or list_ebooks(search="algorithm")
2. Identify book_id (e.g., 321)
3. send_book_to_kindle(book_id=321, format="AZW3")
4. Generate thumbnail: pdf_to_image or epub_to_image
5. Save: data/document/thumbnail/Algorithms-Book.jpg
6. Display: ![Kindle](data/document/thumbnail/Algorithms-Book.jpg)
7. Message: "✅ Sent 'Introduction to Algorithms' to your Kindle!"
```

### Example 4: Library Search and Export
```
User: "Find all Python books and export them"

1. search_books("title:Python")
2. Display results with IDs
3. For each book:
   - export_book(book_id=X, output_directory="data/document/python-books/")
4. Confirm count and location
```

## Format Compatibility

### Kindle Devices
- ✅ Best: MOBI, AZW3
- ⚠️ OK: PDF (less optimal)
- ❌ No: EPUB (must convert)

### Generic E-Readers
- ✅ Best: EPUB
- ⚠️ OK: PDF
- ❌ Limited: MOBI (some devices)

### Computer/Tablet
- ✅ All formats supported with appropriate software

## Best Practices

1. **Always search before adding** - Avoid duplicates
2. **Use consistent metadata** - Clean titles and author names
3. **Convert before sending to Kindle** - Prefer MOBI/AZW3 over PDF
4. **Generate thumbnails for Kindle sends** - Visual confirmation is helpful
5. **Tag books appropriately** - Makes searching easier
6. **Export before sharing** - Don't share library paths directly
7. **Check format compatibility** - Convert if needed
8. **Verify email settings** - Required for Kindle delivery
9. **Clean up attachments** - Remove from attachment folder after adding to library
10. **Use book IDs** - More reliable than searching by title multiple times

## Integration with Document Management

Ebook management integrates with document management:

1. **Upload Flow**: attachment → Calibre → library
2. **Export Flow**: library → data/document/ → share
3. **Thumbnail Flow**: Kindle send → thumbnail → confirmation
4. **Organization**: Use content-based naming for exports

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| Book not found | Wrong search term | Try broader search or list all |
| Conversion failed | Unsupported format | Check source format compatibility |
| Kindle send failed | Email not configured | Verify .env settings |
| Duplicate book | Already in library | Search before adding |
| Format not available | Book not in that format | Convert first |
| Export failed | Invalid path | Check output_directory exists |

## Privacy and Organization

- Keep personal library organized with proper metadata
- Use tags for categories (fiction, technical, reference, etc.)
- Maintain consistent author naming
- Back up library periodically
- Clean up temporary exports after use
