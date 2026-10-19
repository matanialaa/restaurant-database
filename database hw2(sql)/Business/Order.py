from datetime import datetime
from typing import Optional


class Order:
    def __init__(self, order_id: Optional[int] = None, date: Optional[datetime] = None) -> None:
        self.__order_id = order_id
        self.__datetime = date

    def get_order_id(self) -> Optional[int]:
        return self.__order_id

    def set_order_id(self, order_id: int) -> None:
        self.__order_id = order_id

    def get_datetime(self) -> Optional[datetime]:
        return self.__datetime

    def set_datetime(self, date: datetime) -> None:
        self.__datetime = date

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Order):
            return False
        return self.__order_id == __value.__order_id and self.__datetime == __value.__datetime

    def __str__(self) -> str:
        return f'order_id={self.__order_id}, date={self.__datetime}'

class BadOrder(Order):
    def __init__(self) -> None:
        super().__init__(order_id=-1, date=datetime.min)
