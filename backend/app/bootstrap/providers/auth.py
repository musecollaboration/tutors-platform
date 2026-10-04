from dishka import Provider, Scope, provide

from app.core.config import Settings
from app.modules.auth.application.ports.refresh_token_repository import RefreshTokenRepository
from app.modules.auth.application.ports.token_service import TokenService
from app.modules.auth.application.use_cases.login import Login
from app.modules.auth.application.use_cases.logout import Logout
from app.modules.auth.application.use_cases.refresh import Refresh
from app.modules.auth.infrastructure.adapters import JwtTokenService
from app.modules.auth.infrastructure.repositories import SqlAlchemyRefreshTokenRepository


class AuthProvider(Provider):
    """Dishka provider for the auth module."""

    scope = Scope.REQUEST

    refresh_token_repository = provide(
        SqlAlchemyRefreshTokenRepository,
        provides=RefreshTokenRepository,
    )
    login = provide(Login)
    refresh = provide(Refresh)
    logout = provide(Logout)

    @provide(scope=Scope.APP)
    def provide_token_service(self, settings: Settings) -> TokenService:
        return JwtTokenService(
            secret_key=settings.jwt_secret_key,
            algorithm=settings.jwt_algorithm,
            access_expire_minutes=settings.access_token_expire_minutes,
            refresh_expire_days=settings.refresh_token_expire_days,
        )
