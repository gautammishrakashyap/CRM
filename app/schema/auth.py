from pydantic import BaseModel
from fastapi import Form
from typing import Annotated


class LoginForm(BaseModel):
    """Simple login form with only username and password"""
    username: str
    password: str


def get_login_form(
    username: Annotated[str, Form()],
    password: Annotated[str, Form()]
) -> LoginForm:
    """Dependency to get login form data with only username and password"""
    return LoginForm(username=username, password=password)