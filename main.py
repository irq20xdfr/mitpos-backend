from dotenv import load_dotenv
load_dotenv()

import os
import json
import tempfile

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from db import insert_product_sale, get_inventory, add_elements_to_inventory, confirm_element_db, add_product_to_inventory_db, \
        decrease_inventory_quantity, get_product_info_db, update_product_info_db, delete_from_inventory_db, update_name_and_description_db

from utils.ia import get_text_in_photo, get_products_in_photo

from utils.misc import send_notification

app = FastAPI()

PRODUCT_NOTIFICATION_THRESHOLD = int(os.environ.get("PRODUCT_NOTIFICATION_THRESHOLD"))

class ProductSale(BaseModel):
    name: str
    size: str
    price: float
    quantity: int
    barcode: str

@app.post("/products")
async def create_item(item: ProductSale):
    insert_product_sale(item.name, item.size, item.price, item.quantity, item.barcode)
    current_quantity = decrease_inventory_quantity(item.barcode, item.quantity)
    update_product_info_db(item)

    if current_quantity <= PRODUCT_NOTIFICATION_THRESHOLD:
        send_notification(f"Quedan {current_quantity} unidades de {item.name}", f"Debe ir previniendo comprar más de {item.name}")

    return JSONResponse(
        content={"message": "Product sale added successfully"},
        media_type="application/json; charset=utf-8"
    )
    

@app.post("/parse-product-data")
async def upload_image(image: UploadFile = File(...)):
    try:
        # Create a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            contents = await image.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name

            data = get_text_in_photo(temp_file_path)

            parsed_data = json.loads(data.replace("```json", "").replace("```", ""))

            return JSONResponse(
                content={"data": parsed_data},
                media_type="application/json; charset=utf-8"
            )
    except Exception as e:
        if 'temp_file_path' in locals():
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error parsing image: {str(e)}")
    
@app.post("/products-in-photo")
async def find_products_in_photo(image: UploadFile = File(...)):
    items = []
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as temp_file:
            contents = await image.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name

            inventory = get_inventory()
            names = [item['name'] for item in inventory]

            items_str = get_products_in_photo(temp_file_path, names)
            items = json.loads(items_str.replace("```json", "").replace("```", ""))
            print(items)
            add_elements_to_inventory(items)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing image: {str(e)}")
    
    return JSONResponse(
        content={"items": items},
        media_type="application/json; charset=utf-8"
    )
    
@app.get("/inventory")
async def get_all_items_inventory():
    inventory = get_inventory()
    return JSONResponse(
        content={"inventory": inventory},
        media_type="application/json; charset=utf-8"
    )

@app.post("/confirm-element")
async def confirm_element(data: dict):
    id = data.get('id')
    if id is None:
        raise HTTPException(status_code=400, detail="Missing 'id' in request body")
    res = confirm_element_db(id)
    return JSONResponse(
        content={"message": "Element confirmed successfully" if res else "Error confirming element"},
        media_type="application/json; charset=utf-8"
    )

@app.post("/add-product-to-inventory")
async def add_product_to_inventory(data: dict):
    barcode = data.get('barcode')
    inventory_id = data.get('inventory_id')
    res = add_product_to_inventory_db(barcode, inventory_id)
    return JSONResponse(
        content={"message": "Product added to inventory successfully" if res else "Error adding product to inventory"},
        media_type="application/json; charset=utf-8"
    )

@app.get("/product-info")
async def get_product_info(barcode: str):
    product_info = get_product_info_db(barcode)
    return JSONResponse(
        content={"has_product": product_info is not None, "product_info": product_info},
        media_type="application/json; charset=utf-8"
    )

@app.delete("/delete-from-inventory")
async def delete_from_inventory(id: int):
    res = delete_from_inventory_db(id)
    return JSONResponse(
        content={"message": "Item deleted from inventory successfully" if res else "Error deleting item from inventory"},
        media_type="application/json; charset=utf-8"
    )

@app.post("/update-name-and-description")
async def update_name_and_description(data: dict):
    id = data.get('id')
    name = data.get('name')
    description = data.get('description')
    res = update_name_and_description_db(id, name, description)
    return JSONResponse(
        content={"message": "Name and description updated successfully" if res else "Error updating name and description"},
        media_type="application/json; charset=utf-8"
    )

@app.post("/send-notification")
async def send_notification_controller(data: dict):
    title = data.get('title')
    body = data.get('body')
    res = send_notification(title, body)
    return JSONResponse(
        content={"message": "Notification sent successfully" if res else "Error sending notification"},
        media_type="application/json; charset=utf-8"
    )