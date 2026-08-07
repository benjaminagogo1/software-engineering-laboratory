personal-finance-tracking-system/
│
├── main.py
│   Entry point of the application. Displays the main menu, handles user choices,
│   and coordinates the overall program flow.
│
├── models.py
│   Contains the application's data models (classes), such as the Expense class,
│   which represents an individual expense.
│
├── tracker.py
│   Contains the ExpenseTracker class. Responsible for all business logic such as
│   adding, searching, updating, deleting, and managing expenses.
│
├── menus.py
│   Contains all menu functions that interact with the user by collecting input,
│   displaying output, and calling the appropriate tracker methods.
│
├── storage.py
│   Handles data persistence, including saving expenses to and loading expenses
│   from the JSON file.
│
├── utils.py
│   Contains reusable helper functions such as input validation, formatting,
│   and other utility functions shared across the project.
│
├── data/
│   Stores the application's persistent data files.
│   │
│   └── expense.json
│       JSON file used to permanently store all expense records.
│
└── README.md
    Project documentation containing the project overview, features, installation
    instructions, usage guide, folder structure, and future improvements.








   ###  python3 -m version-2.0

It failed because of two reasons.

Reason 1: Hyphens (-) are not valid in Python module names

Python sees:

version-2.0

as something like:




version - 2.0

Module names must be valid Python identifiers.

For example, these are valid:

version_2_0
version2
v2


##  Reason 2: -m expects a package

The command

python3 -m package_name

runs a Python package, not just a folder.

A package usually contains an entry point such as:

package_name/
├── __init__.py
└── __main__.py

or another importable module structure.

We haven't built your project that way yet.





# 1. What does "compile" literally mean here?

The word compile literally means:

- Translate code from one language into another language that the computer can execute more efficiently.






- Excellent question. (__The__ answer is yes and __no__.) Python does check some things during compilation, but not nearly as much as Go.

- Let's go through your list one by one.

- Check	Python (Compilation)	Go (Compilation)
- Syntax	✅ Yes	✅ Yes
- Types	❌ No (mostly at runtime)	✅ Yes
- Undefined variables	❌ Usually at runtime	✅ Yes
- Missing imports	⚠️ Imported when execution reaches them	✅ Yes
- Unused variables	❌ No	✅ Yes (compile error)
- Function signatures	❌ Mostly at runtime	✅ Yes
- Package dependencies	⚠️ Imported when needed	✅ Yes

Let's understand each one.

1. Syntax ✅

Python must check syntax before it can even compile to bytecode.

Example:

print("Hello"

Python immediately says:

SyntaxError

Nothing runs.

Go does exactly the same.

2. Types ❌

Python does not check types before running.

Example:

def add(a, b):
    return a + b

Python happily accepts this.

Later:

add(5, "Rice")

Only when this line executes does Python complain:

TypeError

Go would refuse to compile.

3. Undefined variables ❌

Python:

print("Start")

print(x)

Output:

Start
NameError: name 'x' is not defined

It only discovers x doesn't exist when execution reaches that line.

Go would reject the program before it starts.

4. Missing imports ⚠️

Suppose:

import mymodule

If mymodule doesn't exist:

Python raises:

ModuleNotFoundError

But notice something subtle.

It happens when Python executes the import statement, not during a whole-program compilation phase like Go.

5. Unused variables ❌

Python doesn't care.

x = 100
print("Hello")

Runs perfectly.

Go:

x := 100
fmt.Println("Hello")

Compile error:

x declared and not used

Go forces you to keep your code clean.

6. Function signatures ❌

Python allows:

def add(a, b):
    return a + b

This compiles.

Only later:

add(5)

does Python complain:

TypeError:
missing 1 required positional argument

Go checks this before running.

7. Package dependencies ⚠️

Go checks every package before running.

Python imports modules as execution progresses.

If a module can't be found, execution stops at that point.

The biggest difference

Think of Go as an inspector.

Before opening a restaurant:

✓ Kitchen?
✓ Tables?
✓ Staff?
✓ Electricity?
✓ Water?

Everything okay?

Open.

Nothing happens until every check passes.

Python is different.

It opens the restaurant immediately.

Customer walks in.

Chef starts cooking.

Then suddenly:

Oops!

We don't have rice.

Restaurant stops at that moment.

The professional term

You've just discovered one of the biggest differences between programming languages.

## Go

- Most errors are detected statically.

Meaning:

- Before the program runs.

## Python

- Many errors are detected dynamically.

Meaning:

- While the program is running.

- Benjamin, this distinction—static vs. dynamic checking—is one of the foundational concepts in programming language design. We'll encounter it again when we discuss type systems, compilers, and interpreters in more depth. Understanding it now will make many future topics much easier to grasp.

If I remembered correctly, u said go discard compiled code, does that mean it compiled everytime?

Yes—but there's an important distinction between go run and go build.

## Case 1: go run ✅

When you type:

go run .

Go roughly does this:

Read source code
        ↓
Compile everything
        ↓
Create a temporary executable
        ↓
Run it
        ↓
Delete the temporary executable

So yes, go run compiles every time you run it.

The executable is temporary and is discarded after the program exits.

## Case 2: go build ✅

When you type:

go build

Go does this:

Read source code
        ↓
Compile everything
        ↓
Create a permanent executable

For example:

expense-tracker

Then you run it directly:

./expense-tracker

At this point, no compilation happens. You're just executing the already-built machine code.

Does Go always compile from scratch?

Not exactly.

This is another clever optimization.

Go maintains a build cache.

If a package hasn't changed, Go can reuse previously compiled package data instead of recompiling everything. So while go run always performs a build step before execution, it often doesn't need to recompile every unchanged package from scratch.

Compare Python and Go
Python
Run program
      ↓
Compile changed .py files to bytecode
      ↓
Store .pyc in __pycache__
      ↓
Run

Python caches bytecode.

Go
go run
      ↓
Compile packages (reusing build cache when possible)
      ↓
Create temporary executable
      ↓
Run
      ↓
Delete executable

Go caches compiled package artifacts, but the temporary executable created by go run is discarded.

The key takeaway
python main.py → compiles to bytecode (and caches it in __pycache__).
go run . → builds a native executable (using the build cache when possible), runs it, then deletes the temporary executable.
go build → builds a native executable once, and you can run that executable repeatedly without rebuilding until you change the source code.

This is one of the fundamental differences between the Python and Go development workflows, and you've started noticing it from your own experiments rather than just reading about it.

Is it then mean that Go des not have bytecode?

Correct. Go does not have a bytecode stage like Python or Java.

This is a very important distinction.

Let's compare them.

Python
main.py
   │
   ▼
Compile
   │
   ▼
Bytecode (.pyc)
   │
   ▼
Python Virtual Machine (PVM)
   │
   ▼
CPU

Python always goes through bytecode.

Java
Main.java
   │
   ▼
Compile
   │
   ▼
Bytecode (.class)
   │
   ▼
Java Virtual Machine (JVM)
   │
   ▼
CPU

Java also uses bytecode.

Go
main.go
   │
   ▼
Compile
   │
   ▼
Machine Code
   │
   ▼
CPU

Notice what is missing?

There is no bytecode and no virtual machine.

The Go compiler generates native instructions that your CPU understands directly.

Then why does Go compile?

Because compiling does not automatically mean creating bytecode.

Remember our definition:

### Compilation is translating one language into another.

The target language depends on the compiler.

For example:

## Language	Compiles To
- Python - Bytecode
- Java	- Bytecode
- Go	Machine code
- C	Machine code
- Rust	Machine code

## Why did Python choose bytecode?

Imagine Python generated machine code like Go.

Every operating system has a different instruction set and executable format.

You would need a different build for:

- Windows
- Linux
- macOS

Instead, Python compiles to a portable bytecode.

As long as a machine has the Python interpreter (specifically the Python Virtual Machine), it can execute the same .py program.

## Why did Go avoid bytecode?

Go's designers wanted:

- Maximum execution speed
- Small deployment footprint
- No virtual machine
- Easy distribution

When you compile a Go program:

go build

you usually get a single executable like:

expense-tracker

You can copy that executable to another Linux machine with the same architecture, and it can often run without installing Go because the machine code is already inside it.

Python can't do that with a .py file alone—it requires a compatible Python interpreter to execute the bytecode.

The bigger picture

You have now encountered the three major execution models used by modern languages:

## 1. Interpreted / Bytecode VM
---------------------------------
1. Python
2. Java (JVM)
3. C#

Source
   ↓
Bytecode
   ↓
Virtual Machine
   ↓
CPU


## 2. Ahead-of-Time (AOT) Compilation
----------------------------------
1. Go
2. C
3. Rust

Source
   ↓
Machine Code
   ↓
CPU


3. Just-In-Time (JIT) Compilation
---------------------------------
1. Modern Java
2. Modern C#
3. JavaScript engines (V8)

Source
   ↓
Bytecode
   ↓
Virtual Machine
   ↓
Machine Code (while running)
   ↓
CPU

Over the coming months, we'll explore all three models in depth. Understanding these execution pipelines will help you reason about performance, portability, deployment, and why different languages make different design choices.





1. Interpreted / Bytecode VM
---------------------------------
Python
Java (JVM)
C#

Source
   ↓
Bytecode
   ↓
Virtual Machine
   ↓
CPU


2. Ahead-of-Time (AOT) Compilation
----------------------------------
Go
C
Rust

Source
   ↓
Machine Code
   ↓
CPU


3. Just-In-Time (JIT) Compilation
---------------------------------
Modern Java
Modern C#
JavaScript engines (V8)

Source
   ↓
Bytecode
   ↓
Virtual Machine
   ↓
Machine Code (while running)
   ↓
CPU




Version 1
Programming

↓

Version 2
Modular Programming

↓

Version 3
Data Modeling

↓

Version 4
Object-Oriented Design

↓

Version 5
Testing

↓

Version 6
Database

↓

Version 7
REST API

↓

Version 8
Authentication

↓

Version 9
Docker

↓

Version 10
Deployment

↓

Production