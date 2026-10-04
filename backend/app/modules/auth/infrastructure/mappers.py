from app.modules.auth.domain.entities.refresh_token import RefreshToken
from app.modules.auth.infrastructure.models import RefreshTokenModel


def refresh_token_to_entity(model: RefreshTokenModel) -> RefreshToken:
    """Convert RefreshTokenModel to RefreshToken entity."""
    return RefreshToken(
        _id=model.id,
        _user_id=model.user_id,
        _token_hash=model.token_hash,
        _expires_at=model.expires_at,
        _created_at=model.created_at,
        _revoked_at=model.revoked_at,
    )


def refresh_token_to_model(entity: RefreshToken) -> RefreshTokenModel:
    """Convert RefreshToken entity to RefreshTokenModel."""
    return RefreshTokenModel(
        id=entity.id,
        user_id=entity.user_id,
        token_hash=entity.token_hash,
        expires_at=entity.expires_at,
        created_at=entity.created_at,
        revoked_at=entity.revoked_at,
    )
