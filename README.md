# eposfederatorwebapi
EPOS federator service


Install the basic libraries
```
pip install git+https://github.com/mlmarius/eposfederatorlibs.git
```

Install the main web api
```
pip install git+https://github.com/mlmarius/eposfederatorwebapi.git
```

Install plugins that perform the actual federation

## Radon plugin
```
pip install git+https://github.com/mlmarius/eposfederatorradon.git
```

# Run the app
```
python -m eposfederator.webapi run
```

access the service index on http://localhost:8888/services
