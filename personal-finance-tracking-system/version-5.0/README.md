7. This is called serialization

The process:

Python object
      ↓
JSON-compatible representation
      ↓
JSON



And the reverse:

JSON
 ↓
Python data
 ↓
Python object

is called deserialization.

So our Repository is currently doing something like:

        DESERIALIZATION
JSON ─────────────────────► Expense
                 

        SERIALIZATION
Expense ──────────────────► JSON






┌─────────────────────────────┐
│ UI                          │
│ User input validation       │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Service                     │
│ Business operations         │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Model                       │
│ What makes an Expense valid │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Repository                  │
│ Persistence / retrieval     │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│ Storage                     │
│ JSON file I/O               │
└─────────────────────────────┘