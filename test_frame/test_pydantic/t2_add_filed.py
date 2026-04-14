

from pydantic import BaseModel, BaseConfig

class NoExtraFieldsConfig(BaseConfig):
    # allow_mutation = False
    extra = "forbid"

class MyModel(BaseModel):


    name: str
    age: int

    # __config__ = NoExtraFieldsConfig

    class Config:
        extra = "forbid"

# Create an instance
obj = MyModel(name="John", age=30)

# Subclass attempts to add extra fields
class SubModel(MyModel):
    extra_field: bool

# Attempt to create subclass instance
sub_obj = SubModel(name="Jane", age=25, extra_field=True)  # Raises error: pydantic.error_wrappers.ValidationError