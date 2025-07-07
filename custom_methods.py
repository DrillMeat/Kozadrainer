from aiogram.methods.base import TelegramMethod
from typing import List
from pydantic import BaseModel, Field


class StarAmount(BaseModel):
    star_amount: int = Field(..., alias="amount")


class OwnedGift(BaseModel):
    owned_gift_id: str
    gift: dict  # Базовая информация о подарке
    type: str = "regular"  # "regular" или "unique"


class OwnedGifts(BaseModel):
    gifts: List[OwnedGift]


class GetFixedBusinessAccountStarBalance(TelegramMethod[StarAmount]):
    __returning__ = StarAmount
    __api_method__ = "getBusinessAccountStarBalance"

    business_connection_id: str


class GetFixedBusinessAccountGifts(TelegramMethod[OwnedGifts]):
    __returning__ = OwnedGifts
    __api_method__ = "getBusinessAccountGifts"

    business_connection_id: str

class TransferGift(TelegramMethod[bool]):
    __returning__ = bool
    __api_method__ = "transferGift"

    business_connection_id: str
    owned_gift_id: str
    new_owner_chat_id: int
    star_amount: int = 25  # Комиссия за передачу подарка в звездах


class ConvertGiftToStars(TelegramMethod[bool]):
    __returning__ = bool
    __api_method__ = "convertGiftToStars"

    business_connection_id: str
    owned_gift_id: str


class UpgradeGift(TelegramMethod[bool]):
    __returning__ = bool
    __api_method__ = "upgradeGift"

    business_connection_id: str
    owned_gift_id: str


class TransferBusinessAccountStars(TelegramMethod[bool]):
    __returning__ = bool
    __api_method__ = "transferBusinessAccountStars"

    business_connection_id: str
    star_amount: int


class StarsRevenueWithdrawalUrl(BaseModel):
    url: str


class GetStarsRevenueWithdrawalUrl(TelegramMethod[StarsRevenueWithdrawalUrl]):
    __returning__ = StarsRevenueWithdrawalUrl
    __api_method__ = "getStarsRevenueWithdrawalUrl"

    peer: str  # InputPeer - можно использовать "me" для себя
    stars: int  # количество звезд для вывода
    password: str  # InputCheckPasswordSRP - пароль 2FA