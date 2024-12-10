from fastapi import FastAPI, Depends, Request, Body
from sqlalchemy.orm import Session
from model import ReviewTable, UserTable, StoreTable, OrderTable, MenuTable
from db import session
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
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

order_history.add_middleware(SessionMiddleware, secret_key="your-secret-key")

def get_db():
    db = session()
    try:
        yield db
    finally:
        db.close()

#로그인 상태 확인, 로그인 중인 유저 아이디 반환
@order_history.get("/check_login/")
async def check_login(request: Request):
    # 세션에서 사용자 정보 확인
    if "user_id" not in request.session:
        return False
    
    return {"user_id": f"{request.session['user_id']}"}

#가게 아이디로 가게의 모든 메뉴 아이디들을 반환
@order_history.get("/menu_ids/{store_id}")
async def get_menu_ids(store_id: int, db: Session = Depends(get_db)):
    menu_ids = db.query(MenuTable.menu_id).filter(MenuTable.store_id == store_id).all()
    
    return {"menu_ids": [menu_id[0] for menu_id in menu_ids]}

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

#재주문 버튼 처리, 새로운 order_id반환
@order_history.post("/order/increase/")
async def increase_order_quantity(user_id: str = Body(...), menu_id: int = Body(...), store_id: int = Body(...), db: Session = Depends(get_db)):
    order = db.query(OrderTable).filter(OrderTable.user_id == user_id).first()
    
    if order:
        order.quantity += 1
        db.commit()
        db.refresh(order)
        return {"order_id": order.order_id}

    else:
        new_order = OrderTable(
            user_id=user_id,
            store_id = store_id,
            menu_id=menu_id,
            quantity=1,
            is_completed=False,
        )
        db.add(new_order)
        db.commit()
        db.refresh(new_order)
        return {"order_id": new_order.order_id}

if __name__ == "__order_history__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port)