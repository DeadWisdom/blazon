== Blazon ==



== MyPy ==

 - mypy runs as a linter
 - only checks functions that have type annotations
 - will not coerce an iterator into a list
   - it really shouldn't because the function might need to operate on a list in place
   - it can't because it does nothing at runtime


== Static Typing vs Schema Typing ==

  - Static typing only thinks about the type or class, nothing more / no metadata.
  - Schema typing can provide all sorts of constraints and metadata that allow the data
    to interface with various systems
  - Static typing is for compilers that need to know how to structure blocks of data, not for humans
    to understand the form data should have, nor their significance.
  - short, int, long, long long -- all describe the same primitive data-type but need extra names
    because there is no mechanism for metadata
  - string describes a type, ip-address describes the form of the data
  - classes, structs, unions allow more information / metadata but now you are creating
    indirection / abstractions which should always be minimized
  - schema typing relates directly to data storage making mapping a breeze, you can even set
    metadata for data storage, for instance configuring a field to be nullable, indexable, a
    primary key, or a reference to a primary key

== Coercion ==

  Type systems do not convert implicitly because it might not be what the user wants.
  Blazon so far does do this, because most of the time the user doesn't care.
  How can we handle the case where we do care?
  Perhaps we can have some markers for zero-copy, or pass by reference, or maybe mark something
  as no-coercion.

== Steps ==

  - setup a project that uses mypy and an ide with type hinting
  - make sure it works with blazon
  - make blazon take any python data-type for 'type'
  - make constraints only native, convert to other systems, but not work in the other systems
  - other systems must create transformations that map from native (e.g. type)
  - other systems can create extensions (constraints only for them)

== Problems ==

  - Have a problem in splendor where we need to transform the schema definitions from native
    to json schema... Certain constraints need to transform a subschema, this causes a problem.
    The solution is to move from a networked constraint model to a hub and spoke, with the native
    schema being the spoke.  Being able to convert to various other systems is simply a function of
    transforming from the spoke.