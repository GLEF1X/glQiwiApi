from aiohttp.abc import AbstractAccessLogger


class AccessLogger(AbstractAccessLogger):
    """ Custom logger for aiohttp.web.Application """

    def log(self, request, response, time) -> None:
        self.logger.info(f'{request.remote} '
                         f'"{request.method} {request.path} '
                         f'done in {time}s: {response.status}')
