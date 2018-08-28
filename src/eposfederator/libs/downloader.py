import logging
import aiohttp
import aiohttp.client_exceptions
import asyncio
from aiostream import stream
import json


logger = logging.getLogger(__name__)


class DownloadError(Exception):

    def __init__(self, message, url, status=None, response_text=None):
        super().__init__(message)
        self.url = url
        self.status = status
        self.response_text = response_text

    def to_dict(self):
        out = {
            "mesage": str(self),
            "url": self.url
        }
        if self.status:
            out['status'] = self.status
        if self.response_text:
            out['response_text'] = self.response_text
        return out

    def to_json(self):
        return json.dumps(self.to_dict())


def json_response_validator(resp, **kwargs):
    content_type = kwargs.get('content-type', 'application/json')
    status = kwargs.get('status', 200)
    if resp.headers.get('Content-Type') != content_type or resp.status != status:
        raise DownloadError(
            "Invalid json response from NFO",
            url=resp.url
        )


async def fetch(url, **kwargs):
    logger.info(f"fetching from {url}")
    timeout = kwargs.get('timeout', aiohttp.ClientTimeout(total=kwargs.get('timeout_total', 20)))
    response_validator = kwargs.get('response_validator', json_response_validator)
    extractor = kwargs.get('extractor', json_extractor)
    try:
        async with aiohttp.ClientSession(timeout=timeout) as session:
            try:
                async with session.get(url) as resp:
                    try:
                        response_validator(resp)
                        logger.info("validated the response")
                        async for batch in extractor(resp):
                            logger.info("got response batch")
                            yield batch
                            return
                    except Exception as e:
                        if resp.content_type.lower() == 'application/json':
                            yield DownloadError(
                                str(e),
                                url,
                                status=resp.status,
                                response_text=json.loads(await(resp.text()))
                            )
                        return
            except Exception as e:
                yield DownloadError(str(e), url)
                return
    except Exception as e:
        yield DownloadError(str(e), url)

    logger.info("download complete")


class DownloadManager(object):

    def __init__(self, *args):
        self._urls = args
        self.errors = []

    async def fetch(self, *args, **kwargs):
        gens = [fetch(url, **kwargs) for url in self._urls]
        async with stream.merge(*gens).stream() as chunks:
            async for chunk in chunks:
                if isinstance(chunk, bytes):
                    yield chunk
                elif isinstance(chunk, Exception):
                    self.errors.append(chunk)


async def merge(*iterators):
    ''' alternative to aiostream.merge '''
    its = [itr.__aiter__() for itr in iterators]
    while True:
        pending = set()
        for idx, it in enumerate(its):
            if it is None:
                continue
            fut = asyncio.ensure_future(it.__anext__())
            fut._merge_id = idx
            pending.add(fut)
        if len(pending) is 0:
            break
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            for fut in done:
                try:
                    ret = fut.result()
                except StopAsyncIteration:
                    its[fut._merge_id] = None
                    continue
                yield ret


async def json_extractor(resp, **kwargs):  # noqa
    chunk_size = kwargs.get('chunk_size', 1000)
    output_buffer_max_size = kwargs.get('output_buffer_max_size', 20000)
    level = 0
    seek = True
    output_buffer = bytearray()

    obj_start = ord(b'{')
    obj_end = ord(b'}')
    result_end = ord(b']')

    # fetch chunks from the response and process them
    while True:
        crt = bytearray(await resp.content.read(chunk_size))
        if not crt:
            # no more inbound data to process
            break
        if seek:
            idx = 0
            try:
                idx = crt.index(b"[") + 1
                del crt[:idx]
                seek = False
            except ValueError:
                continue

        # process each character in the chunk
        while True:
            try:
                char = crt.pop(0)
            except IndexError:
                break

            if char is obj_start:
                level += 1
            elif char is obj_end:
                level -= 1

            output_buffer.append(char)

            # each time level is 0, we have zero or more
            # complete objects in the output buffer
            if level is 0:
                if len(output_buffer) > output_buffer_max_size or char is result_end:
                    if char is result_end:
                        output_buffer.pop(-1)
                    yield bytes(output_buffer)
                    output_buffer = bytearray()
