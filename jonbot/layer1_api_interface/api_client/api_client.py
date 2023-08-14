import asyncio
import logging
from typing import Union, Callable, List, Coroutine

import aiohttp

from jonbot.layer1_api_interface.helpers.error_message_from_response import error_message_from_response
from jonbot.models.api_endpoint_url import ApiRoute
from jonbot.system.environment_config.environment_variables import API_HOST_NAME

logger = logging.getLogger(__name__)


class ApiClient:
    api_host_name = API_HOST_NAME

    async def send_request_to_api(self,
                                  endpoint_name: str,
                                  data: dict = None,
                                  type: str = "POST") -> dict:
        try:
            endpoint_url = ApiRoute.from_endpoint(host_name=self.api_host_name,
                                                  endpoint=endpoint_name).endpoint_url

            if not data:
                data = {}
            logger.debug(f"Sending request to API endpoint: {endpoint_url} with payload keys: {list(data.keys())}")
            async with aiohttp.ClientSession() as session:
                if type == "POST":
                    response = await session.post(endpoint_url, json=data)
                elif type == "GET":
                    response = await session.get(endpoint_url, json=data)
                else:
                    raise Exception(f"Invalid type: {type}")

                if response.status == 200:
                    return await response.json()
                else:
                    error_message = await error_message_from_response(response)
                    logger.exception(error_message)
                    raise Exception(error_message)
        except Exception as e:
            error_msg = f"An error occurred while sending a request to the API: {str(e)}"
            logger.exception(error_msg)
            raise

    async def send_request_to_api_streaming(self,
                                            endpoint_name: str,
                                            data: dict = dict(),
                                            callbacks: Union[Callable, Coroutine] = None) -> list():
        endpoint_url = ApiRoute.from_endpoint(host_name=self.api_host_name,
                                              endpoint=endpoint_name).endpoint_url
        if not callbacks:
            callbacks = []

        if not data:
            data = {}

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint_url, json=data) as response:
                    if response.status == 200:
                        async for line in response.content.iter_any():
                            await run_callbacks(callbacks, line)
                    else:
                        error_message = await error_message_from_response(response)
                        logger.error(error_message)
                        await run_callbacks(callbacks, error_message.encode('utf-8'))
                        raise Exception(error_message)
        except Exception as e:
            error_msg = f"An error occurred while streaming from the API: {str(e)}"
            logger.exception(error_msg)
            await run_callbacks(callbacks, error_msg.encode('utf-8'))
            raise


async def run_callbacks(callbacks: List[Callable], line: bytes):
    try:
        for callback in callbacks:
            logger.trace(f"Running callback: {callback.__name__}")
            if asyncio.iscoroutinefunction(callback):
                await callback(line.decode('utf-8').strip())
            else:
                callback(line.decode('utf-8').strip())
    except Exception as e:
        logger.exception(f"An error occurred while running a callback: {str(e)}")
        raise
