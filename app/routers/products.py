from typing import Annotated
from sqlalchemy.orm import Session
from app.backend.db_depends import get_db
from sqlalchemy import insert
from slugify import slugify

from sqlalchemy import insert, select, update

from fastapi import APIRouter, Depends, status, HTTPException

from app.models import Category
from app.models.products import Product
from app.schemas import CreateProduct

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
async def all_products(db: Annotated[Session, Depends(get_db)]):
    products = db.scalars(select(Product)
            .filter(Product.is_active == True, Product.stock > 0)).all()
    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no product"
        )
    return products


@router.post('/create')
async def create_product(db: Annotated[Session, Depends(get_db)], product_data: CreateProduct):
    db.execute(insert(Product).values(
        name=product_data.name,
        slug=slugify(product_data.name),
        description=product_data.description,
        price=product_data.price,
        image_url=product_data.image_url,
        stock=product_data.stock,
        category_id=product_data.category,
        rating=0.0
    ))
    db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.get('/{category_slug}')
async def product_by_category(db: Annotated[Session, Depends(get_db)], category_slug: str):
    category = db.scalar(select(Category).where(Category.slug == category_slug))
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    subcategories = db.scalars(select(Category).where(Category.parent_id == category.id)).all()
    all_categories = [category] + subcategories
    category_ids = [cat.id for cat in all_categories]
    products = db.scalars(
        select(Product)
        .where(
            Product.category_id.in_(category_ids),
            Product.is_active == True,
            Product.stock > 0
        )
    ).all()
    return products



@router.get('/detail/{product_slug}')
async def product_detail(db: Annotated[Session, Depends(get_db)], product_slug: str):
    product = db.scalar(select(Product).where(Product.slug == product_slug))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no product"
        )
    return product


@router.put('/detail/{product_slug}')
async def update_product(product_slug: str, db: Annotated[Session, Depends(get_db)],
                         upd_product: CreateProduct ):
    product = db.scalar(select(Product).where(Product.slug == product_slug))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    product.name = upd_product.name
    product.description = upd_product.description
    product.price = upd_product.price
    product.image_url = upd_product.image_url
    product.stock = upd_product.stock
    product.category_id = upd_product.category

    db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product update is successful'
    }


@router.delete('/delete/{product_slug}')
async def delete_product(product_slug: str, db: Annotated[Session, Depends(get_db)]):
    product = db.scalar(select(Product).where(Product.slug == product_slug))
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    product.is_active = False
    db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product delete is successful'
    }