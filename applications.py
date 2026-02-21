"""
FastAPI main application class.
"""
from typing import Any, Dict, List, Optional, Sequence, Tuple, Type, Union

from fastapi import routing
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
from fastapi.types import ASGIApp


class FastAPI:
    """
    The main FastAPI application class.

    This is the class that you would normally use to create your FastAPI application.

    ## Example

    ```python
    from fastapi import FastAPI

    app = FastAPI()

    @app.get("/")
    async def read_root():
        return {"Hello": "World"}
    ```
    """

    def __init__(
        self,
        *,
        debug: bool = False,
        routes: Optional[List[routing.BaseRoute]] = None,
        title: str = "FastAPI",
        description: str = "",
        version: str = "0.1.0",
        openapi_url: Optional[str] = "/openapi.json",
        openapi_tags: Optional[List[Dict[str, Any]]] = None,
        servers: Optional[List[Dict[str, Union[str, Any]]]] = None,
        docs_url: Optional[str] = "/docs",
        redoc_url: Optional[str] = "/redoc",
        swagger_ui_oauth2_redirect_url: Optional[str] = "/docs/oauth2-redirect",
        swagger_ui_init_oauth: Optional[Dict[str, Any]] = None,
        middleware: Optional[Sequence[Middleware]] = None,
        exception_handlers: Optional[Dict[Union[int, Type[Exception]], Any]] = None,
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        terms_of_service: Optional[str] = None,
        contact: Optional[Dict[str, Union[str, Any]]] = None,
        license_info: Optional[Dict[str, Union[str, Any]]] = None,
        openapi_prefix: str = "",
        root_path: str = "",
        root_path_in_servers: bool = True,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        callbacks: Optional[List[Dict[str, Any]]] = None,
        webhooks_url: Optional[str] = None,
    ) -> None:
        self.debug: bool = debug
        self.state: Dict[str, Any] = {}
        self.router: routing.APIRouter = routing.APIRouter(
            routes=routes,
            dependency_overrides_provider=self,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            default_response_class=None,
        )
        self.title = title
        self.description = description
        self.version = version
        self.terms_of_service = terms_of_service
        self.contact = contact
        self.license_info = license_info
        self.openapi_url = openapi_url
        self.openapi_tags = openapi_tags
        self.servers = servers
        self.root_path = root_path
        self.root_path_in_servers = root_path_in_servers
        self.responses = responses
        self.callbacks = callbacks
        self.webhooks_url = webhooks_url
        self.docs_url = docs_url
        self.redoc_url = redoc_url
        self.swagger_ui_oauth2_redirect_url = swagger_ui_oauth2_redirect_url
        self.swagger_ui_init_oauth = swagger_ui_init_oauth
        self.openapi_prefix = openapi_prefix
        self.middleware = list(middleware) if middleware else []
        self.exception_handlers = exception_handlers or {}
        self.user_middleware = []
        self.routes = []
        self._setup()

    def _setup(self) -> None:
        if self.openapi_url:
            self.add_route(self.openapi_url, self.openapi, include_in_schema=False)
        if self.openapi_url and self.docs_url:
            self.add_route(self.docs_url, self.swagger_ui_html, include_in_schema=False)
        if self.openapi_url and self.redoc_url:
            self.add_route(self.redoc_url, self.redoc_html, include_in_schema=False)
        if self.openapi_url and self.swagger_ui_oauth2_redirect_url:
            self.add_route(
                self.swagger_ui_oauth2_redirect_url,
                self.swagger_ui_oauth2_redirect,
                include_in_schema=False,
            )

    def add_middleware(
        self,
        middleware_class: Type[ASGIApp],
        **options: Any,
    ) -> None:
        self.user_middleware.insert(0, Middleware(middleware_class, **options))

    def add_route(
        self,
        path: str,
        route: routing.BaseRoute,
        **kwargs: Any,
    ) -> None:
        self.router.routes.append(route)

    def include_router(
        self,
        router: routing.APIRouter,
        *,
        prefix: str = "",
        tags: Optional[List[str]] = None,
        dependencies: Optional[Sequence[routing.Depends]] = None,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        default_response_class: Optional[Type[routing.Response]] = None,
        callbacks: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self.router.include_router(
            router,
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            responses=responses,
            default_response_class=default_response_class,
            callbacks=callbacks,
        )

    async def __call__(self, scope: Dict[str, Any], receive: Any, send: Any) -> None:
        await self.router(scope, receive, send)

    def openapi(self) -> Dict[str, Any]:
        if not self.openapi_schema:
            self.openapi_schema = get_openapi(
                title=self.title,
                version=self.version,
                description=self.description,
                routes=self.routes,
                tags=self.openapi_tags,
                servers=self.servers,
                terms_of_service=self.terms_of_service,
                contact=self.contact,
                license_info=self.license_info,
            )
        return self.openapi_schema

    def swagger_ui_html(self) -> Any:
        return get_swagger_ui_html(
            openapi_url=self.openapi_url,
            title=self.title + " - Swagger UI",
            oauth2_redirect_url=self.swagger_ui_oauth2_redirect_url,
            init_oauth=self.swagger_ui_init_oauth,
        )

    def redoc_html(self) -> Any:
        return get_redoc_html(
            openapi_url=self.openapi_url,
            title=self.title + " - ReDoc",
        )

    def swagger_ui_oauth2_redirect(self) -> Any:
        return {"detail": "OAuth2 redirect"}
