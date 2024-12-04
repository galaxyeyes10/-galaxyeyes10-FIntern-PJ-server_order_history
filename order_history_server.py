from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from model import ReviewTable, UserTable, StoreTable, OrderTable, MenuTable
from db import session
from fastapi.middleware.cors import CORSMiddleware
import os
import uvicorn


order_history = FastAPI()

order_history.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False, 
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

#사진, 수량, 메뉴 이름, 가격 딕셔너리 반환
@order_history.get("/order_history/{user_id}")
async def read_order_history(user_id: str, db: Session = Depends(get_db)):
    orders = db.query(
                        OrderTable.order_date,
                        MenuTable.menu_img,
                        OrderTable.quantity,
                        MenuTable.menu_name,
                        MenuTable.price 
                        ).join(MenuTable, OrderTable.menu_id == MenuTable.menu_id).filter(OrderTable.user_id == user_id, MenuTable.is_main == "true", OrderTable.is_completed == "true").all()
    sides = db.query(
                        MenuTable.menu_img,
                        OrderTable.quantity,
                        MenuTable.menu_name,
                        MenuTable.price
                        ).join(MenuTable, OrderTable.menu_id == MenuTable.menu_id).filter(OrderTable.user_id == user_id, MenuTable.is_main == "false", OrderTable.is_completed == "true").all()
    history = [
        {
            "date": str(order.order_date)[:10],
            "img": order.menu_img,
            "quantity": order.quantity,
            "menu_name": order.menu_name,
            "price": order.price * order.quantity
        }
        for order in orders
    ]
    side_history = [
        {
            "img": side.menu_img,
            "quantity": side.quantity,
            "menu_name": side.menu_name,
            "price": side.price * side.quantity
        }
        for side in sides
    ]

    return history + side_history

#재주문 버튼 처리
if __name__ == "__order_history__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)