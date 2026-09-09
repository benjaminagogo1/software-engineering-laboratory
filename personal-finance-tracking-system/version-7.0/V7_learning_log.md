A log level tells us how important or severe that event is.

For example:

INFO     → normal important event
WARNING  → something unusual, but the application can continue
ERROR    → something failed
CRITICAL → serious failure affecting the system
DEBUG    → detailed information useful during development

A log message tells us what happened.

Step 6: What is a logger?

The logger is the part of the logging system that your application talks to.


Step 8: What is a handler?

We've said the logger doesn't decide the final destination by itself.

The handler is responsible for taking a log record and sending it somewhere.

So the distinction is:

Logger → receives the event from your application.
Handler → determines where that log record is sent.

Step 9: What is a formatter?

A formatter determines how a log record looks when it is written.

Logger = receives the event
Handler = sends the record somewhere
Formatter = controls how the record looks

A logger is named so we can identify where a log event came from.



What does __name__ mean?

In:

logger = logging.getLogger(__name__)

__name__ is a special Python variable.

Python automatically gives every module a __name__ value that identifies that module.


import logging

logger = logging.getLogger(__name__)



Multiple handlers

A logger can have more than one handler, and each handler can send logs to a different destination.

For example:

Logger
  ├── FileHandler      → app.log
  └── StreamHandler    → terminal

So one message:

logger.info("Expense added")

could go to both places.

Now the handler levels become useful.

For example:

Logger = DEBUG

FileHandler = INFO
Terminal    = DEBUG

Then:

DEBUG    → terminal only
INFO     → terminal + file
WARNING  → terminal + file
ERROR    → terminal + file

This gives us a powerful idea:

One logger can produce a log record, while different handlers decide where that record goes and what level each destination receives.



Log rotation

Right now, V7 writes everything into:

logs/app.log

But imagine the application runs for months or years.

The file could become:

app.log → 500 MB
app.log → 2 GB
app.log → 20 GB

That's a problem.

Log rotation solves this by automatically creating new log files when the current one reaches a certain size or age.

For example:

logs/
├── app.log
├── app.log.1
├── app.log.2
└── app.log.3

The newest logs stay in app.log, while older logs are moved into rotated files.

Why this matters

Without rotation:

Log file grows forever.

With rotation:

Log files remain within a controlled size/retention policy.

Python's logging module provides handlers specifically for this, such as RotatingFileHandler.


There are actually two common kinds of rotation:

Size-based rotation → rotate when file becomes too large
Time-based rotation → rotate after a period of time



Time-based rotation

TimedRotatingFileHandler works similarly to RotatingFileHandler, but the trigger is time instead of file size.

TimedRotatingFileHandler(
    LOG_FILE,
    when="midnight",
    backupCount=7
)



## V7 is not the final architecture. It is one stage in the deliberate progression toward V11.


If a logger handles its own records and should not send them to its ancestors, disable propagation.


Modules create log records.
Central configuration decides how those records are handled.