<p align="center">
  <img width="64" src="https://avatars2.githubusercontent.com/u/22204821?s=200&v=4" alt="Rehive Logo">
  <h1 align="center">Django Rehive Extras</h1>
  <p align="center">Extra utilities for using Django.</p>
</p>

## Features

- Python 3.6
- Money model field using decimals.
- Date model with created/updated field.
- State model that stores the previous state of a model instance in memory.
- Cascading archive model class.
- Integrated model class that supports date, state and cascading archives.


## Getting started

1. Install the package:

```sh
pip install django-rehive-extras
```

2. Add "django_rehive_extras" to your INSTALLED_APPS settings like this:

```python
INSTALLED_APPS = [
    ...
    'django_rehive_extras',
]
```
