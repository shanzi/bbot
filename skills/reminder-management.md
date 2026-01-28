---
name: reminder-management
description: Create, manage, and track reminders and scheduled tasks. Set timers for future notifications, list pending reminders, and cancel scheduled tasks.
---

# Reminder Management

Create and manage reminders that will proactively notify users at specified times.

## How Reminders Work

When you create a reminder:
1. It's stored in a file with trigger time and message
2. The bot checks reminders periodically in the background
3. When the trigger time arrives, the bot simulates a message to you
4. You then process it and send the reminder message to the user
5. The reminder is marked as "triggered"

## Available Operations

### 1. Add Reminder

Create a new reminder or scheduled task.

**Tool:** `add_reminder`

**Parameters:**
- `message` - What to remind the user about
- `trigger_time` - When to send the reminder

**Time Formats:**

**Relative Time (Easy):**
- `+30m` - In 30 minutes
- `+2h` - In 2 hours
- `+1d` - In 1 day
- `+7d` - In 7 days

**Absolute Time (ISO format):**
- `2026-01-28T15:30:00` - Specific date and time
- `2026-02-01T09:00:00` - Future date

**Examples:**
```
User: "Remind me in 30 minutes to check the oven"
→ add_reminder(message="Check the oven", trigger_time="+30m")

User: "Set a reminder for tomorrow at 9am"
→ add_reminder(message="Daily standup meeting", trigger_time="2026-01-29T09:00:00")

User: "Remind me in 2 hours to call mom"
→ add_reminder(message="Call mom", trigger_time="+2h")
```

### 2. List Reminders

View all reminders for the current chat.

**Tool:** `list_reminders`

**Parameters:**
- `status` - Optional filter: "pending", "triggered", "cancelled", or "all"

**Status Types:**
- **pending** ⏰ - Waiting to trigger
- **triggered** ✅ - Already sent to user
- **cancelled** ❌ - User cancelled before triggering

**Examples:**
```
User: "Show my reminders"
→ list_reminders(status="all")

User: "What reminders are coming up?"
→ list_reminders(status="pending")

User: "Show triggered reminders"
→ list_reminders(status="triggered")
```

### 3. Cancel Reminder

Cancel a pending reminder before it triggers.

**Tool:** `cancel_reminder`

**Parameters:**
- `reminder_id` - ID of the reminder to cancel

**Process:**
1. List reminders to show IDs
2. User selects which to cancel
3. Cancel by ID
4. Confirm cancellation

**Example:**
```
User: "Cancel that reminder"

1. list_reminders(chat_id=123, status="pending")
2. Show: "Which reminder would you like to cancel? (ID 5, ID 7, ID 12)"
3. User: "Cancel 7"
4. cancel_reminder(reminder_id=7)
5. Confirm: "✅ Reminder 7 cancelled"
```

## Workflow Patterns

### Pattern 1: Simple Timer
```
User: "Set a timer for 15 minutes"

1. add_reminder(
     message="Timer finished! 15 minutes are up.",
     trigger_time="+15m"
   )
2. Response: "⏰ Timer set for 15 minutes. I'll notify you at 3:45 PM."
```

### Pattern 2: Task Reminder
```
User: "Remind me to submit the report by 5pm today"

1. Calculate 5pm today in ISO format: "2026-01-28T17:00:00"
2. add_reminder(
     message="Time to submit the report!",
     trigger_time="2026-01-28T17:00:00"
   )
3. Response: "✅ Reminder set for 5:00 PM today: Submit the report"
```

### Pattern 3: Future Event
```
User: "Remind me about the meeting next Monday at 10am"

1. Calculate next Monday 10am: "2026-02-03T10:00:00"
2. add_reminder(
     message="Meeting reminder: Time for your scheduled meeting",
     trigger_time="2026-02-03T10:00:00"
   )
3. Response: "📅 Reminder set for Monday, Feb 3 at 10:00 AM"
```

### Pattern 4: List and Cancel
```
User: "What reminders do I have?"

1. list_reminders(status="pending")
2. Display reminders with IDs and times
3. User: "Cancel the one about the dentist"
4. Identify reminder ID (e.g., 8)
5. cancel_reminder(reminder_id=8)
6. Confirm cancellation
```

## Time Parsing

### Understanding User Requests

**Common Patterns:**
- "in X minutes/hours/days" → Use relative time (+Xm, +Xh, +Xd)
- "at HH:MM" (today) → Calculate ISO format for today
- "tomorrow at HH:MM" → Calculate ISO format for tomorrow
- "next [day] at HH:MM" → Calculate ISO format for that day
- "on [date] at HH:MM" → Parse date and create ISO format

**Examples:**
```
"in 30 minutes" → "+30m"
"in 2 hours" → "+2h"
"in 1 day" → "+1d"
"at 3pm" → "2026-01-28T15:00:00" (if today)
"tomorrow at 9am" → "2026-01-29T09:00:00"
"next Friday at 2pm" → "2026-01-31T14:00:00"
```

### Time Calculation Helper

Use the `time` MCP server to help with calculations:
- Get current time
- Calculate future dates
- Handle timezone conversions

## Reminder Message Best Practices

### Good Reminder Messages

Clear, actionable, and contextual:

✅ **Good Examples:**
- "Time to check the oven - your cookies have been baking for 15 minutes"
- "Meeting reminder: Daily standup in 5 minutes"
- "Don't forget: Call mom about weekend plans"
- "Task reminder: Submit the quarterly report by 5pm"

❌ **Bad Examples:**
- "Reminder" (too vague)
- "Thing" (no context)
- "Do the thing you said" (unclear)

### Include Context

When creating reminders, include enough context so the message is useful:
- What to do
- Why it matters
- Any relevant details from the conversation

**Example:**
```
User: "Remind me to water the plants in 2 days, they need it after I repotted them"

Good message: "Water the plants - they need attention after repotting 2 days ago"
Bad message: "Water plants"
```

## Status Display

Format reminder lists clearly:

```
📋 Your Reminders:

⏰ ID: 5 | Status: pending
   Message: Check the oven
   Trigger: 2026-01-28 15:30:00
   Created: 2026-01-28 15:00:00

⏰ ID: 7 | Status: pending
   Message: Call mom
   Trigger: 2026-01-28 17:00:00
   Created: 2026-01-28 14:45:00

✅ ID: 3 | Status: triggered
   Message: Meeting reminder
   Trigger: 2026-01-28 09:00:00
   Created: 2026-01-27 18:00:00
```

## Handling Triggered Reminders

When a reminder triggers (you receive a simulated message from the bot):

1. **Acknowledge the trigger**
   - You'll receive context about which reminder triggered
   - The reminder ID and original message will be provided

2. **Send notification to user**
   - Create a friendly, clear notification
   - Include the reminder message
   - Add context if helpful

3. **Reminder is auto-marked as triggered**
   - Bot handles status update
   - No need to manually update

**Example Trigger Response:**
```
Received: "REMINDER_TRIGGER: ID 5 - Check the oven"

Send to user: "⏰ Reminder: Check the oven! You set this reminder 30 minutes ago."
```

## Edge Cases

### Past Times
Cannot create reminders in the past:
```
User: "Remind me at 2pm" (it's already 3pm)
→ Error: "Cannot set reminder in the past"
→ Ask: "Did you mean 2pm tomorrow?"
```

### Ambiguous Times
Clarify with user:
```
User: "Remind me at 3"
→ Ask: "Do you mean 3:00 AM or 3:00 PM?"
→ Or default to PM during daytime, AM during nighttime
```

### Multiple Reminders
Handle batch requests:
```
User: "Remind me to take medicine at 8am, 2pm, and 8pm daily"
→ Create 3 separate reminders (daily recurrence not yet implemented)
→ Or: Create 3 reminders for tomorrow at those times
→ Inform user about each one
```

## Limitations

**Current Limitations:**
1. **No Recurrence** - Cannot create "daily", "weekly" reminders yet
2. **No Timezone Specification** - Uses server timezone
3. **No Reminder Editing** - Must cancel and recreate to change
4. **No Snooze** - Cannot postpone after triggering

**Workarounds:**
- For recurring: Create multiple reminders manually
- For timezone: Calculate correct time before adding
- For editing: Cancel old, create new
- For snooze: User can ask to create new reminder after trigger

## Integration with Other Skills

Reminders work well with:

- **Time Server**: Calculate exact trigger times
- **Calendar**: Schedule based on dates
- **Tasks**: Remind about deadlines
- **Document Management**: Remind to review documents
- **SMS**: Remind to respond to messages

## Best Practices

1. **Always confirm reminder details** - Show trigger time to user
2. **Use clear, actionable messages** - User should know what to do
3. **Prefer relative times for short delays** - Easier than calculating exact time
4. **Use absolute times for specific events** - Better for scheduled meetings
5. **Include context in messages** - Make reminders self-explanatory
6. **List reminders when asked** - Help users track what's scheduled
7. **Explain cancellation** - Confirm which reminder was cancelled
8. **Handle ambiguity** - Ask for clarification on unclear times
9. **Check for conflicts** - Warn if many reminders at similar times
10. **Be proactive** - Suggest reminders for mentioned tasks

## Example Conversations

### Example 1: Quick Timer
```
User: "Set a 10 minute timer"
Agent: Uses add_reminder with +10m
Agent: "⏰ Timer set! I'll notify you in 10 minutes at 3:40 PM."
```

### Example 2: Daily Task
```
User: "Remind me to take vitamins tomorrow morning at 8am"
Agent: Calculates tomorrow 8am ISO time
Agent: Uses add_reminder
Agent: "✅ Reminder set for tomorrow at 8:00 AM: Take vitamins"
```

### Example 3: Manage Reminders
```
User: "What reminders do I have?"
Agent: Uses list_reminders
Agent: Shows 3 pending reminders with IDs and times
User: "Cancel the 2pm one"
Agent: Identifies ID 7 is at 2pm
Agent: Uses cancel_reminder(7)
Agent: "✅ Cancelled reminder: Meeting with John"
```

### Example 4: Multiple Reminders
```
User: "I need to prep for the presentation. Remind me to practice in 1 hour, then review slides in 2 hours"
Agent: Creates two reminders
Agent:
"✅ Created 2 reminders:
1. Practice presentation - 3:30 PM (in 1 hour)
2. Review slides - 4:30 PM (in 2 hours)"
```

## Security & Privacy

- Reminders are stored globally and shared across all users
- The bot maintains a mapping to route notifications to the correct chat
- All users can see all reminders when listing (consider limiting this in production)
- Reminder messages stored in plain text in data/reminders/reminders.json
- Consider privacy when storing sensitive reminder content
- For multi-user deployments, consider filtering list_reminders by chat context
