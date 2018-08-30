import tornado.ioloop
import tornado.web
import logging
import signal
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

def merge(source, destination):
    '''deeply merge dictionaries'''
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination

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

    for entrypoint in pkg_resources.iter_entry_points(group='eposfederator.federators'):
        extension = entrypoint.load()
        config.APPCONFIG['plugins'][extension.ID] = extension
        config_path = pkg_resources.resource_filename(extension.__name__, 'settings.yml')
        crt_config = config.load_yaml(config_path)
        if crt_config['plugins'][extension.ID].get('is_active') is True:
            config.USERCONFIG = merge(config.USERCONFIG, crt_config)
        else:
            logging.info(f"{extension.ID} is not ACTIVE !!!")
        handlers.extend(
            [(f"{extension.BASE_ROUTE}/{handler.ROUTE}", handler) for handler in extension.HANDLERS]
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
    # logging.info("USERCONFIG")
    # logging.info(config.USERCONFIG)
    # logging.info("\n\n\n")
    # logging.info("APPCONFIG")
    # logging.info(config.APPCONFIG)

    handler_map = {}

    if 'plugins' in config.USERCONFIG:
        for plugin_id, plugin_config in config.USERCONFIG['plugins'].items():
            logging.info(f"Adding {plugin_id} to config")
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
                        "service_id": f"{plugin_id}.{endpoint_id}",
                        "url": backend_config.get('url'),
                        "handler": handler
                    })
    else:
        logging.info("no plugins found!!!")

    logging.info("REGISTERED SERVICES:")
    for service in serviceindex.__SERVICES__:
        logging.info(service)
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
