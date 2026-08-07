Module
  ↓
Module is an object
  ↓
Object has a namespace
  ↓
Namespace contains names
  ↓
Names refer to objects
  ↓
Functions receive references to objects
  ↓
Different namespaces can contain the same name
  ↓
Those names can still refer to the same object


The object carries its relationship to its class, even though the class definition lives in another module/file.



Each part of the system should have a focused responsibility and should not unnecessarily depend on the internal details of other parts.

1. Cohesion — "Does this component belong together?"

Cohesion asks:

Are the responsibilities inside this module closely related?
2. Coupling — "How dependent are these components?"

Coupling asks:

How much does one component depend on the internal details of another?


What is abstraction?

At its simplest:

Abstraction means exposing what another part needs to know while hiding how it is implemented.