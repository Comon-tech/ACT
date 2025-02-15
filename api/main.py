import logging
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import fastapi
import uvicorn
import uvicorn.server
from colorama import Fore
from discord.ext.commands import Bot
from fastapi import FastAPI, Request

from utils.log import LOG_CONFIG, logger
from utils.misc import text_block

from .routes import add_routes

log = logger(__name__)


# ----------------------------------------------------------------------------------------------------
# * ACT API
# ----------------------------------------------------------------------------------------------------
class ActApi(FastAPI):
    def __init__(self, bot: Bot = None, url="", *args, **kwargs):
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
        self.server = uvicorn.Server(
            uvicorn.Config(
                self,
                host=self.address.hostname,
                port=self.address.port,
                log_level="info",
                loop="asyncio",
                log_config=LOG_CONFIG,
            )
        )
        add_routes(self, bot)

    # ----------------------------------------------------------------------------------------------------

    @property
    def info_text(self):
        scheme, netloc = self.address.scheme, self.address.netloc
        full_url = lambda txt="": f"{Fore.BLUE}{scheme}://{netloc}{txt}{Fore.RESET}"
        output = "Links:"
        output += f"\n• Root: {full_url()}"
        output += f"\n• Swagger: {full_url(self.docs_url)}"
        output += f"\n• Redoc: {full_url(self.redoc_url)}"
        output += "\nRoutes:"
        for route in self.routes:
            methods = ",".join(list(route.methods))
            output += (
                f"\n• [{methods}] {Fore.CYAN}{route.path}{Fore.RESET} ({route.name})"
            )
        return text_block(output)

    # ----------------------------------------------------------------------------------------------------

    async def enter(self):
        log.loading(f"{self.title} api running...")
        await self.server.serve()

    async def exit(self):
        log.loading(f"{self.title} api exiting...")
        await self.server.shutdown()
        log.success(f"{self.title} api exited.")
