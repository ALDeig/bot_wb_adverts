from pydantic import BaseModel, Field


class AdsCard(BaseModel):
    scu: int = Field(alias="nmId") 
    position: int
    price: int = Field(alias="cpm")


class Price(BaseModel):
    scu: int
    position: int
    price: int
