from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from app.modules.users.application.use_cases.register_user import RegisterUser
from app.modules.users.presentation.schemas import RegisterUserRequest, RegisterUserResponse

router = APIRouter(
    prefix="/users",
    tags=["users"],
    route_class=DishkaRoute,
)


@router.post("", status_code=status.HTTP_201_CREATED)
async def register_user(
    body: RegisterUserRequest,
    use_case: FromDishka[RegisterUser],
) -> RegisterUserResponse:
    result = await use_case.execute(
        full_name=body.full_name,
        email=body.email,
        password=body.password,
    )
    return RegisterUserResponse.from_dto(result)
