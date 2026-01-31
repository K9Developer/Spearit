import re


def validate_email(email: str) -> bool:
    email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if re.match(email_regex, email):
        return True
    return False

def validate_username(username: str) -> bool:
    if 3 <= len(username) <= 128:
        return True
    return False

def validate_password(password: str) -> bool:
    if len(password) < 8:
        return False
    return True