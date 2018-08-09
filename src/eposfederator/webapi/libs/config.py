from ruamel.yaml import YAML, parser as yaml_parser
from collections import defaultdict
import logging

# store our configs in here
USERCONFIG = {}
APPCONFIG = defaultdict(dict)

def load_yaml(filepath):
    yaml = YAML(typ='safe')   # default, if not specfied, is 'rt' (round-trip)
    with open(filepath, 'rt') as f:
        try:
            return yaml.load(f)
        except yaml_parser.ParserError as e:
            logging.info(e)
            raise


def update_config(filepath):
    USERCONFIG.update(load_yaml(filepath))

def dump_yml():
    import io
    output = io.StringIO()
    yml = YAML(typ='safe', pure=True)  # 'safe' load and dump
    with io.StringIO() as f:
        yml.dump(USERCONFIG, f)
        return f.getvalue()
