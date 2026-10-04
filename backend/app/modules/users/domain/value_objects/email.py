import re
from dataclasses import dataclass

from app.modules.users.domain.exceptions import InvalidEmailError

# Пробельные и управляющие символы запрещены в любой части адреса.
_CONTROL_OR_SPACE = re.compile(r"[\s\x00-\x1f\x7f]")

# Локальная часть: разрешённые ASCII-символы, точка не по краям и не подряд.
_LOCAL_PART = re.compile(r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[A-Za-z0-9!#$%&'*+/=?^_`{|}~-]+)*$")

# Лейбл домена: длина 1..63, дефис не по краям. Не-ASCII разрешён: интернационализированные
# домены отсекает граница (EmailStr), домен не должен ломать чтение уже сохранённых значений.
_DOMAIN_LABEL = re.compile(r"^[A-Za-z0-9\u00a1-\uffff](?:[A-Za-z0-9\u00a1-\uffff-]{0,61}[A-Za-z0-9\u00a1-\uffff])?$")

_MAX_LOCAL_LEN = 64
_MAX_DOMAIN_LEN = 253
_MAX_EMAIL_LEN = 254


@dataclass(frozen=True, slots=True)
class Email:
    """Email address. Normalized on creation, immutable afterwards."""

    value: str

    def __post_init__(self) -> None:
        normalized = self.value.strip().lower()
        self._validate(normalized)
        object.__setattr__(self, "value", normalized)

    def _validate(self, value: str) -> None:
        if len(value) > _MAX_EMAIL_LEN or _CONTROL_OR_SPACE.search(value):
            raise self._fail()

        local, sep, domain = value.partition("@")
        if not sep or "@" in domain:
            raise self._fail()

        if len(local) > _MAX_LOCAL_LEN or not _LOCAL_PART.match(local):
            raise self._fail()

        if len(domain) > _MAX_DOMAIN_LEN or "." not in domain:
            raise self._fail()

        labels = domain.split(".")
        if any(not _DOMAIN_LABEL.match(label) for label in labels):
            raise self._fail()

        # Числовой TLD — адрес недоставляем.
        if labels[-1].isdigit():
            raise self._fail()

    def _fail(self) -> InvalidEmailError:
        raise InvalidEmailError(f"Invalid email: {self.value!r}")

    def __str__(self) -> str:
        return self.value
