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


HTTP means Hypertext Transfer Protocol.

It is the set of rules that allows a client and a server to communicate over a network.


Think of HTTP as the communication language


1. FastAPI

FastAPI is a Python web framework for building APIs.

Think of it as a tool/library that helps us create an HTTP API without having to build all the HTTP handling ourselves.





2. RESTful API

REST means Representational State Transfer.

A RESTful API is an API designed according to REST principles.


a REST-style API treats expenses as resources:

GET    /expenses
POST   /expenses
GET    /expenses/5
DELETE /expenses/5

The HTTP method tells us what we want to do, while the URL identifies the resource.

So:

RESTful API = a style/design approach for building APIs.

FastAPI and REST are therefore not competing things.

You can use FastAPI to build a RESTful API.



3. CRUD API

CRUD means:

C — Create
R — Read
U — Update
D — Delete

These are the four basic operations we perform on data.

A CRUD API is simply an API that provides operations for those basic data actions.




3. What are REST principles?

This is the more important question.

REST is not a programming language, framework, or library.

It is a set of architectural principles for designing networked applications, particularly APIs.

The basic idea is:

Treat things in your system as resources, and use standardized HTTP mechanisms to interact with those resources.

For our application, an expense is a resource.

So instead of designing our API around functions:

/addExpense
/getExpenses
/updateExpense
/deleteExpense

we design it around the resource:

/expenses

Then HTTP methods describe what we want to do with that resource:

POST   /expenses       → create an expense
GET    /expenses       → retrieve expenses
GET    /expenses/5     → retrieve expense 5
PUT    /expenses/5     → replace expense 5
DELETE /expenses/5     → delete expense 5

That's one of the most visible REST principles.

Another important REST idea: statelessness

Each request should contain the information the server needs to process that request.

For example:

GET /expenses/5

The server shouldn't have to remember:

“Oh, Benjamin previously asked about expense 5, so I know what he means.”

The request itself identifies what is being requested.


HTTP gives us standardized things such as:

Method — what kind of operation is being requested.
URL — where the request is going.
Headers — additional information about the request.
Body — data being sent, when necessary.
Status code — tells the client what happened.



Client
  │
  │ JSON
  ↓
API
  │
  │ Python objects/data
  ↓
Service
  │
  ↓
Database



And on the way back:
Database
  ↓
Service
  ↓
API
  │
  │ JSON
  ↓


Don't confuse JSON with REST.

REST → architectural principles for designing the API.
JSON → a format for representing the data exchanged.
HTTP → the communication protocol.
FastAPI → the Python framework we'll use to build the API.


So why use JSON?

Because the client and server need a common, standardized way to represent structured data.



Imagine the client wants to send:

name = Food
amount = 1000

We need some agreed format for representing that information.

JSON provides one:

And importantly, JSON is language-independent.


The client could be:

JavaScript
Go
Python
Java
Mobile app

while our server is Python.

They don't need to use the same programming language. They just agree to exchange data using JSON.

But JSON isn't mandatory

This is important.

HTTP does not require JSON.

A request body could contain:

JSON
XML
plain text
form data
binary data
images/files
etc.

JSON is simply very convenient for structured API data, which is why it is extremely common in modern APIs.

So the fundamental reason is:

JSON gives different programs a common, language-independent representation for structured data.




Is it JSON that is language agnostic or it is API?

JSON is language-agnostic. An API can also be designed to be language-independent, but that's a different idea.

JSON

JSON is a data format. It defines a standard way to represent data:

{
  "name": "Food",
  "amount": 1000
}

Python, Go, JavaScript, Java, etc. can all read and produce JSON.

That's why we call JSON language-agnostic: it isn't tied to one programming language.

API

An API is an interface that allows one piece of software to interact with another.

An API isn't inherently language-agnostic or language-specific.

For example, our API could be built with Python/FastAPI, while the client could be written in Go. They can communicate because they agree on things like:

HTTP
JSON
API rules

So:

JSON = language-agnostic data format.

API = interface/contract for software communication, which can be consumed by programs written in different languages.


A schema is a definition of the shape and rules of data that an API expects or returns.

The key idea: a schema is the contract for the structure of data.

Pydantic is a Python library that lets us define the structure and validation rules for data.






FastAPI is not part of Python's standard library, so our project needs the FastAPI package.

We also need an ASGI (Asynchronous Server Gateway Interface) server to run the application. We'll use Uvicorn, a server commonly used with FastAPI.

FastAPI
→ provides the API framework

Uvicorn
→ runs the FastAPI application as a web server


ASGI (Asynchronous Server Gateway Interface) is a standard/interface specification that defines how a Python web server communicates with a Python web application.

Uvicorn is a server implementation that supports ASGI.



ASGI
→ the specification/interface

Uvicorn
→ a server that implements/supports ASGI

FastAPI
→ a web framework that provides an ASGI application


What is Swagger UI?

Swagger UI is a web interface for exploring and testing an API.


OpenAPI is the standardized description of your API.

Swagger UI is the visual interface that uses that description.


## Next step

- Authentication
- Authorization
- Database migrations
- Configuration management
- Environment separation
- API security
- Automated API testing
- Deployment
- External services
- Concurrency
- Transactions
- Caching
- Background tasks
- Monitoring
- CI/CD



Request models define the contract for data coming into the API. Response models define the contract for data leaving the API.


What is TestClient?

TestClient is a testing tool provided through FastAPI's testing support.

## check the commit date 
git log -1 --format=fuller