import importlib
import pkgutil
import logging
import inspect

logger = logging.getLogger(__name__)


def collect_handlernames(packagename):
    logger.info(f"collecting handlers for package {packagename}")
    module = importlib.import_module(packagename)
    # logger.info(f"module path is {module.__path__}")
    for submodule in pkgutil.walk_packages(module.__path__):
        yield submodule.name


def collect_handlers(modulename):
    for submodulename in collect_handlernames(modulename):
        submodule = importlib.import_module(f"{modulename}.{submodulename}")
        logger.info(submodule)
        for name, obj in inspect.getmembers(submodule, inspect.isclass):
            if hasattr(obj, 'ROUTE'):
                yield obj
