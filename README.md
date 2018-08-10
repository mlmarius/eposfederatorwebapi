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

# EXAMPLES

## querying the radon federated api if the radon plugin is installed:
```
http://localhost:8888/radon/?mintime=2010-03-01T00:00:00.000Z&maxtime=2010-05-01T00:00:00.000Z&minlat=43.1&maxlat=43.8&minlon=12.1&maxlon=12.8&min_period=60&max_period=180&type_site=indoor
```
