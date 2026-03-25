
import requests
from pydantic import BaseModel

from dataclasses import dataclass

@dataclass
class User:
    name: str       # Required field (no default value)
    age: int = 18   # Optional field (has default value)

class MyModel(BaseModel):
    name: str
    age: int
    sex: str
    address: str
    phone: str
    email: str

class CommonKls:
    def __init__(self,name,sex,age):
        pass

if __name__ == '__main__':
    m = MyModel(name='Zhang San', age=18, sex='Male',
                address='Chaoyang District, Beijing', phone='13800138000',email='123456@qq.com')
    print(m)



    CommonKls(name='Zhang San', sex='Male', age=18)
