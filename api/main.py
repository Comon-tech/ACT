from contextlib import asynccontextmanager
from typing import cast
from urllib.parse import urlparse

import uvicorn
import uvicorn.server
from colorama import Fore
from discord.ext.commands import Bot
from fastapi import FastAPI
from starlette.routing import Route

from utils.log import LOG_CONFIG, logger
from utils.misc import text_block

from .routes import add_routes

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * ACT API
# ----------------------------------------------------------------------------------------------------
class ActApi(FastAPI):
    def __init__(self, bot: Bot | None = None, url="", *args, **kwargs):
        @asynccontextmanager
        async def lifespan(self: ActApi):
            try:
                log.success(
                    f"🦄 API server connected at {self.address.hostname}:{self.address.port}."
                )
                log.info("\n" + self.info_text)
            except Exception as e:
                log.error(e)
            yield

        super().__init__(lifespan=lifespan, *args, **kwargs)
        self.bot = bot
        self.address = urlparse(url)
        host, port = self.address.hostname or "", self.address.port or 0
        self.server = uvicorn.Server(
            uvicorn.Config(
                self,
                host=host,
                port=port,
                log_level="info",
                loop="asyncio",
                log_config=LOG_CONFIG,
            )
        )
        if bot:
            add_routes(self, bot)

    # ----------------------------------------------------------------------------------------------------

    @property
    def info_text(self):
        scheme, netloc = self.address.scheme, self.address.netloc
        full_url = lambda txt=None: f"{Fore.BLUE}{scheme}://{netloc}{txt}{Fore.RESET}"
        output = "Links:"
        output += f"\n• Root: {full_url()}"
        output += f"\n• Swagger: {full_url(self.docs_url)}"
        output += f"\n• Redoc: {full_url(self.redoc_url)}"
        output += "\nRoutes:"
        for route in self.routes:
            route = cast(Route, route)
            methods = ",".join(list(route.methods or []))
            output += (
                f"\n• [{methods}] {Fore.CYAN}{route.path}{Fore.RESET} ({route.name})"
            )
        return text_block(output)

    # ----------------------------------------------------------------------------------------------------

    async def open(self):
        log.loading(f"API server opening...")
        await self.server.serve()

    async def close(self):
        log.loading(f"API server closing...")
        await self.server.shutdown()
        log.success(f"API server closed.")
