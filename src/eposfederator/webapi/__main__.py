import tornado.ioloop
import tornado.web
import logging
import signal
import importlib
import pkgutil
import argparse
from eposfederator.webapi.libs import config
import os
from eposfederator.libs import serviceindex
from eposfederator.libs import appbuilder
import pkg_resources


logging.basicConfig(
    format='%(asctime)s,%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s',
    datefmt='%d-%m-%Y:%H:%M:%S',
    level=logging.DEBUG
)
# logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger(__name__)

# gather all available handler
# create the application and add urispecs
# perform application initialization


def sig_exit(signum, frame):
    logging.warning('App received exit signal')
    tornado.ioloop.IOLoop.instance().add_callback_from_signal(do_stop, signum, frame)


def do_stop(signum, frame):
    logging.warning('Exiting application')
    tornado.ioloop.IOLoop.instance().stop()


def make_app(args): # noqa
    settings = dict(
        autoreload=True,
        compiled_template_cache=False,
        static_hash_cache=False,
        serve_traceback=True,
        cookie_secret="Ana$r3MereG1n44r3PERE",
        xsrf_cookies=True
    )
    handlers = [(f"{h.ROUTE}", h) for h in appbuilder.collect_handlers('eposfederator.webapi.handlers')]
    plugins_module = 'eposfederator.plugins'
    plugins = importlib.import_module(plugins_module)
    # add handlers from all plugins
    logging.info("finding plugins")
    for module_info in pkgutil.walk_packages(plugins.__path__):
        if '.' in module_info.name:
            continue
        logging.info(f"will import {plugins_module}.{module_info.name} from {plugins.__path__}")
        plugin = importlib.import_module(f"{plugins_module}.{module_info.name}")
        config.APPCONFIG['plugins'][plugin.ID] = plugin

        config_path = pkg_resources.resource_filename(f"{plugins_module}.{module_info.name}", 'settings.yml')
        logging.info(config_path)

        config_files = [os.path.join(pth, 'settings.yml') for pth in plugin.__path__]
        for config_file in config_files:
            crt_config = config.load_yaml(config_file)
            if crt_config['plugins'][plugin.ID].get('is_active') is True:
                config.USERCONFIG.update(crt_config)
        handlers.extend(
            [(f"{plugin.BASE_ROUTE}/{handler.ROUTE}", handler) for handler in plugin.HANDLERS]
        )

    # if user suplied custom config file, overwrite everything with user configs
    try:
        config_file = args.config
    except AttributeError:
        config_file = None

    if config_file is not None:
        logging.info(f"Using config from {config_file}")
        config.update_config(config_file)

    # logging.info("\n\n\n")
    # logging.info(config.USERCONFIG)
    # logging.info("\n\n\n")
    # logging.info(config.APPCONFIG)
    for plugin_id, plugin in config.APPCONFIG['plugins'].items():
        logging.info(plugin.HANDLERS)

    handler_map = {}

    if hasattr(config.USERCONFIG, 'plugins'):
        for plugin_id, plugin_config in config.USERCONFIG['plugins'].items():
            for endpoint_id, endpoint_config in plugin_config.get('endpoints', {}).items():
                for backend_id, backend_config in endpoint_config.get('backends', {}).items():
                    key = (plugin_id, endpoint_id)
                    if handler_map.get(key) is None:
                        for handler in config.APPCONFIG['plugins'][plugin_id].HANDLERS:
                            if handler.ID == endpoint_id:
                                handler_map[key] = handler
                                break
                        else:
                            raise Exception(f"Tried to get non existing handler {key}")
                    handler = handler_map[key]
                    serviceindex.add({
                        "nfo_id": backend_id,
                        "geometry": backend_config.get('geometry'),
                        "service_id": endpoint_id,
                        "url": backend_config.get('url'),
                        "handler": handler
                    })
    logging.info(handlers)

    return tornado.web.Application(handlers, **settings)


def config_cmd(args):
    logging.info('running config cmd')
    make_app(args)
    with open(args.outfile, 'wt') as f:
        f.write(config.dump_yml())


def run_app(args):
    from tornado.platform.asyncio import AsyncIOMainLoop
    AsyncIOMainLoop().install()
    signal.signal(signal.SIGINT, sig_exit)
    app = make_app(args)
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Federator APP", prog="eposfederator.webapi")
    subparsers = parser.add_subparsers(dest='cmd', help='Subparsers')

    configcmd = subparsers.add_parser('dumpconfig', help='Dump the config')
    configcmd.add_argument('outfile', help="Output file to which to dump the config")
    configcmd.set_defaults(func=config_cmd)

    runcmd = subparsers.add_parser('run', help="Run the federator server")
    runcmd.add_argument('--config', default=os.environ.get('CONFIGFILE', None), help="Path to config file. If not supplied we will attempt to get the config file path from the CONFIGFILE environment variable. If that is also not availabe we use default internal config.")
    runcmd.set_defaults(func=run_app)

    args = parser.parse_args()
    try:
        args.func(args)
    except AttributeError:
        parser.print_help()