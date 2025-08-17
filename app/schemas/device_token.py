from uuid import UUID
from pydantic import BaseModel


class DeviceTokenRegister(BaseModel):
    token: str
    platform: str  # android / ios


class DeviceTokenRead(BaseModel):
    id: UUID
    token: str
    platform: str

    model_config = {"from_attributes": True} 