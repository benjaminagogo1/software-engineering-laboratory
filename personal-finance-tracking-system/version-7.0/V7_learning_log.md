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