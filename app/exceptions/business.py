class BusinessException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

class NotFoundException(BusinessException):
    pass

class AuthException(BusinessException):
    pass
