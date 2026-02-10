import json
import re

import httpx
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Coroutine,
    Dict,
    Generic,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    TypeVar,
    Union,
    cast,
    overload,
)

from cozepy import CozeInvalidEventError
from cozepy.log import log_debug, log_error
from cozepy.model import HTTPResponse

T = TypeVar("T")

class EYStream(Generic[T]):
    def __init__(
        self,
        raw_response: httpx.Response,
        iters: Iterator[str],
        fields: List[str],
        handler: Callable[[Dict[str, str], httpx.Response], Optional[T]],
    ):
        self._iters = iters
        self._fields = fields
        self._handler = handler
        self._raw_response = raw_response

    @property
    def response(self) -> HTTPResponse:
        return HTTPResponse(self._raw_response)

    def __iter__(self):
        while True:
            event_dict = self._extra_event()
            if not event_dict:
                break
            item = self._handler(event_dict, self._raw_response)
            if item:
                yield item

    def __next__(self):
        while True:
            event_dict = self._extra_event()
            if not event_dict:
                raise StopIteration
            item = self._handler(event_dict, self._raw_response)
            if item:
                return item

    def _extra_event(self) -> Optional[Dict[str, str]]:
        data = {}
        # data = dict(map(lambda x: (x, ""), self._fields))
        try:
            line = next(self._iters).strip()
        except StopIteration:
            return None

        log_debug("receive event, logid=%s, event=%s", self.response.logid, line)
        pattern = r'^\s*data:\s*\{\s*"delta"\s*:\s*"(.+)"}$'

        match = re.match(pattern, line, re.DOTALL)
        from bots import ChatEventType
        if match:
            # data["data"] = json.dumps({"content":match.group(1)})
            data["data"] = match.group(1).encode('utf-8').decode('unicode_escape')
            data["event"] = ChatEventType.GW_MESSAGE_DELTA
        elif line.endswith("[DONE]"):
            data["data"] = line
            data["event"] = ChatEventType.GW_MESSAGE_COMPLETED
        elif "error" in line:
            data["data"] = line
            data["event"] = ChatEventType.ERROR
        else:
            data["data"] = ""
            data["event"] = ChatEventType.GW_MESSAGE_DELTA
        return data

        # while times < len(data):
        #     try:
        #         line = next(self._iters).strip()
        #     except StopIteration:
        #         return None
        #     if line == "":
        #         continue
        #
        #     log_debug("receive event, logid=%s, event=%s", self.response.logid, line)
        #     pattern = r'^\s*data:\s*\{\s*"delta"\s*:\s*(.+?)\s*(?:,\s*\w+|})\s*$'
        #
        #     match = re.match(pattern, line, re.DOTALL)
        #     if match:
        #         delta_part = match.group(1)
        #         log_error("receive event, delta_part=%s", delta_part)
        #
        #     # 获取 delta 值部分
        #     delta_part = match.group(1)
        #
        #     field, value = self._extra_field_data(line, data)
        #     data[field] = value
        #     times += 1
        # return data

    def _extra_field_data(self, line: str, data: Dict[str, str]) -> Tuple[str, str]:
        for field in self._fields:
            if line.startswith(field + ":"):
                if True or data[field] == "":
                    return field, line[len(field) + 1 :].strip()
                else:
                    raise CozeInvalidEventError(field, line, self.response.logid)
        raise CozeInvalidEventError("", line, self.response.logid)