from pydantic import BaseModel


class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class ProductOut(BaseModel):
    id: int
    name: str
    price: float
    total_stock: int
    remaining_stock: int

    class Config:
        from_attributes = True


class SeckillResponse(BaseModel):
    code: int
    message: str
    order_id: str | None = None


class SeckillResultResponse(BaseModel):
    status: str
    product_name: str | None = None


class OrderOut(BaseModel):
    id: str
    product_id: int
    status: str
    created_at: str

    class Config:
        from_attributes = True


class ApiResponse(BaseModel):
    code: int
    data: dict | list | None = None
    message: str = ""
