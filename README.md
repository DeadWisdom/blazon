Blazon
----------

Blazon is a library for assuring data structure and format.

  - It can be used to assure data structure, like 

It can be used to assure data, for instance:

    ```python
    import blazon, json

    with open("users.json") as o:
      user_data = json.load(o)

    user_schema = blazon.json.schema({
      'properties': {
        'name': {'type': 'string'},
        'age': {'type': 'number', 'minValue': 0},
        'email': {'type': 'string', 'format': 'email'}
      }
    })

    users = [user_schema(item) for item in user_data]
    ```

Now you can be sure that users has 3 properties:

  - name: a string value
  - age: a number value that is 0 or higher
  - email: a string that is formated like an email

`blazon.json.schema()` takes any JSON Schema as its argument, and returns a Schema() object, which
is a callable that will convert/validate the data.




It is used both in the processing of
application data like a JSON blob, but also runtime data like class properties and function 
arguments where it becomes a powerful type-checker and facilitates complex type-hinting.

