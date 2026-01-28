---
name: sms-management
description: Query and manage SMS messages from connected Android devices via ADB. Search messages by phone number, read status, date range, and conversation threads.
---

# SMS Management

Access and query SMS messages from a connected Android device through the `sms` MCP server.

## Available Operations

### 1. Query SMS Messages

Search and filter SMS messages using various criteria.

**Tool:** `query_sms`

**Filter Options:**
- `address` - Phone number (with or without country code)
- `read` - Message read status (True/False/None for all)
- `date_from` - Start timestamp in milliseconds
- `date_to` - End timestamp in milliseconds
- `sort_order` - Sort results (ASC/DESC)
- `limit` - Maximum number of results

**Example Queries:**
```python
# Get recent unread messages
query_sms(read=False, sort_order="DESC", limit=10)

# Find messages from specific number
query_sms(address="+1234567890", sort_order="DESC")

# Messages in date range
query_sms(date_from=1640000000000, date_to=1650000000000)
```

### 2. Get Unread Messages

Quickly retrieve all unread messages.

**Tool:** `get_unread_sms`

**Returns:**
- All messages with read status = 0 (unread)
- Sorted by date (most recent first)
- Includes all message details

**Use When:**
- User asks "Do I have new messages?"
- Checking for unread texts
- Getting message count

### 3. List Conversation Threads

View all SMS conversation threads.

**Tool:** `query_sms_threads`

**Returns:**
- List of conversation threads
- Thread IDs for further queries
- Message counts per thread
- Most recent message preview

**Use When:**
- User wants to see all conversations
- Listing active chats
- Finding specific thread ID

### 4. Get Messages in Thread

Retrieve all messages from a specific conversation.

**Tool:** `get_sms_by_thread`

**Parameters:**
- `thread_id` - The conversation thread identifier
- `sort_order` - Sort by date (ASC/DESC)

**Use When:**
- User asks for conversation history
- Reading entire chat thread
- Analyzing message patterns in conversation

### 5. Check Device Connection

Verify ADB device connection status.

**Tool:** `check_adb_connection`

**Returns:**
- Connection status (connected/disconnected)
- Device information if connected
- Error details if connection failed

**Use When:**
- Troubleshooting SMS access
- Initial setup verification
- Connection issues reported

## Message Data Structure

Each SMS message contains:

| Field | Description | Type |
|-------|-------------|------|
| `address` | Phone number | String |
| `body` | Message content | String |
| `date` | Timestamp (milliseconds) | Integer |
| `type` | Message type | Integer (1=inbox, 2=sent) |
| `read` | Read status | Integer (0=unread, 1=read) |
| `thread_id` | Conversation identifier | Integer |

## Common Use Cases

### Use Case 1: Check New Messages
```
User: "Do I have any new messages?"

Actions:
1. Use get_unread_sms()
2. Count results
3. Display summary with senders
4. Show message previews if requested
```

### Use Case 2: Find Messages from Contact
```
User: "Show me messages from +1234567890"

Actions:
1. Use query_sms(address="+1234567890", sort_order="DESC")
2. Display messages in chronological order
3. Indicate read/unread status
4. Show sent vs received
```

### Use Case 3: Search by Date Range
```
User: "Show messages from last week"

Actions:
1. Calculate date_from timestamp (7 days ago)
2. Calculate date_to timestamp (now)
3. Use query_sms(date_from=X, date_to=Y, sort_order="DESC")
4. Display results grouped by day
```

### Use Case 4: View Conversation
```
User: "Show my conversation with John"

Actions:
1. Use query_sms_threads() to find John's thread
2. Use get_sms_by_thread(thread_id=X, sort_order="ASC")
3. Display as conversation format
4. Show timestamps and read status
```

## Date/Time Handling

SMS timestamps are in milliseconds since Unix epoch.

**Converting from Python datetime:**
```python
import time
from datetime import datetime, timedelta

# 7 days ago
date_from = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)

# Now
date_to = int(datetime.now().timestamp() * 1000)
```

**Display Format:**
- Convert milliseconds to human-readable date/time
- Show relative time for recent messages ("2 hours ago")
- Full date for older messages ("Jan 15, 2026")

## Message Types

Interpret the `type` field:

- **1 = Inbox** - Received messages
- **2 = Sent** - Sent messages
- Other types may exist (drafts, outbox, etc.)

**Display Format:**
- Inbox: "From: [phone]"
- Sent: "To: [phone]"

## Read Status

Interpret the `read` field:

- **0 = Unread** - New/unread message
- **1 = Read** - Message has been read

**Visual Indicators:**
- Unread: Use bold or special marker (📩 or 🔵)
- Read: Standard display (✉️ or ⚪)

## Best Practices

1. **Always check connection first** if SMS access fails
2. **Use appropriate limits** to avoid overwhelming output
3. **Format phone numbers consistently** when searching
4. **Handle empty results gracefully** - inform user clearly
5. **Sort by date DESC** for most recent first (default behavior)
6. **Group by thread** when showing multiple conversations
7. **Respect privacy** - summarize sensitive content appropriately
8. **Handle timestamps** - convert to readable format
9. **Indicate message direction** - sent vs received
10. **Show unread count** when relevant

## Error Handling

Common issues and solutions:

| Error | Cause | Solution |
|-------|-------|----------|
| Connection failed | ADB not connected | Run check_adb_connection() |
| No messages found | Wrong filters | Broaden search criteria |
| Invalid date range | Timestamp format | Convert to milliseconds |
| Thread not found | Invalid thread_id | Use query_sms_threads() first |

## Privacy Considerations

When handling SMS data:

1. Summarize content when appropriate (don't show full messages unless requested)
2. Use contact names if available (instead of numbers)
3. Be mindful of sensitive information
4. Respect user's privacy preferences
5. Don't log or store message content unnecessarily

## Integration with Other Skills

SMS management works well with:

- **Document Management**: Save important messages as documents
- **Calendar/Reminders**: Extract dates and create reminders from messages
- **Contacts**: Cross-reference phone numbers with contact names
- **Notifications**: Alert user about important unread messages
