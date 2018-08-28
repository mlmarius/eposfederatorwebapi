from rtree import index
from shapely import geometry


class WebservicePointer(object):

    def __init__(self, nfo_id, service_id, url, handler, geometry=None):
        """Information about a single Webservice API from a particular NFO

        Args:
            nfo_id (str): A string (should be unique) acting as ID for the NFO
                Example: NIEP or INGV
            geometry (shapely.geometry): A geometry describing this NFO/Service
                authoritative area
            service_id (str): A unique string acting as ID for this service
            url(str): String to use as the url in order to access a particular service
                from a particular NFO

            handler (RequestHandler): RequestHandler that will be instantiated to solve this
                query. We pull .SCHEMA and RESPONSE_TYPE among others from here
        """
        self.nfo_id = nfo_id
        self.geometry = geometry
        self.service_name = service_id
        self.url = url
        self.handler = handler

    @classmethod
    def from_dict(cls, d):
        if d.get('geometry') is not None:
            geo = geometry.Polygon(d.get('geometry'))
            return cls(d['nfo_id'], d['service_id'], d['url'], d['handler'], geometry=geo)
        else:
            return cls(d['nfo_id'], d['service_id'], d['url'], d['handler'])

    def __repr__(self):
        return f"({self.nfo_id}|{self.service_name})"


__SERVICES__ = []
__GEOINDEX__ = None


def geoindex():
    global __SERVICES__, __GEOINDEX__
    __GEOINDEX__ = index.Index()
    for idx, service_pointer in enumerate(__SERVICES__):
        __GEOINDEX__.insert(idx, service_pointer.geometry.bounds, obj=service_pointer)


def add(webservice_pointer):
    global __SERVICES__, __GEOINDEX__
    if isinstance(webservice_pointer, WebservicePointer):
        __SERVICES__.append(webservice_pointer)
    else:
        __SERVICES__.append(WebservicePointer.from_dict(webservice_pointer))
    # geoindex should be rebuilt
    __GEOINDEX__ = None


def get(geometry=None, filter_func=None):
    global __SERVICES__, __GEOINDEX__

    # prepare the geoindex if geoindex search is requested and we have no geoindex
    if geometry is not None and __GEOINDEX__ is None:
        geoindex()

    # if user supplied a geometry select only webservices that intersect our supplied geometry
    if geometry:
        results = [pointer.object for pointer in __GEOINDEX__.intersection(geometry.bounds, objects=True)]
    else:
        results = __SERVICES__

    # if no other filter function supplied return everything
    if filter_func is None:
        return results

    # return only results that satisfy the filter_func
    return [pointer for pointer in results if filter_func(pointer) is True]
