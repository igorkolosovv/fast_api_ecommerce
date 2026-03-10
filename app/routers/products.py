from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.db_depends import get_db
from slugify import slugify

from sqlalchemy import insert, select

from fastapi import APIRouter, Depends, status, HTTPException

from app.models import Category
from app.models.products import Product
from app.schemas import CreateProduct

router = APIRouter(prefix='/products', tags=['products'])


@router.get('/')
async def all_products(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.scalars(select(Product).where(Product.is_active == True, Product.stock > 0))
    products = result.all()

    if not products:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There are no products"
        )
    return products


@router.post('/create')
async def create_product(db: Annotated[AsyncSession, Depends(get_db)], product_data: CreateProduct):
    await db.execute(insert(Product).values(
        name=product_data.name,
        slug=slugify(product_data.name),
        description=product_data.description,
        price=product_data.price,
        image_url=product_data.image_url,
        stock=product_data.stock,
        category_id=product_data.category,
        rating=0.0
    ))
    await db.commit()
    return {
        'status_code': status.HTTP_201_CREATED,
        'transaction': 'Successful'
    }


@router.get('/{category_slug}')
async def product_by_category(db: Annotated[AsyncSession, Depends(get_db)], category_slug: str):
    category = await db.scalar(select(Category).where(Category.slug == category_slug))
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )

    subcategories_result = await db.scalars(select(Category).where(Category.parent_id == category.id))
    subcategories = subcategories_result.all()

    all_categories = [category] + subcategories
    category_ids = [cat.id for cat in all_categories]

    products_result = await db.scalars(
        select(Product)
        .where(
            Product.category_id.in_(category_ids),
            Product.is_active == True,
            Product.stock > 0
        )
    )
    products = products_result.all()
    return products


@router.get('/detail/{product_slug}')
async def product_detail(db: Annotated[AsyncSession, Depends(get_db)], product_slug: str):
    product = await db.scalar(
        select(Product).where(
            Product.slug == product_slug,
            Product.is_active == True,
            Product.stock > 0
        )
    )
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product"
        )
    return product


@router.put('/detail/{product_slug}')
async def update_product(
        product_slug: str,
        db: Annotated[AsyncSession, Depends(get_db)],
        update_product_model: CreateProduct
):
    product_update = await db.scalar(select(Product).where(Product.slug == product_slug))
    if not product_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )

    product_update.name = update_product_model.name
    product_update.description = update_product_model.description
    product_update.price = update_product_model.price
    product_update.image_url = update_product_model.image_url
    product_update.stock = update_product_model.stock
    product_update.category_id = update_product_model.category

    await db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product update is successful'
    }


@router.delete('/delete/{product_slug}')
async def delete_product(product_slug: str, db: Annotated[AsyncSession, Depends(get_db)]):
    product_delete = await db.scalar(select(Product).where(Product.slug == product_slug))
    if not product_delete:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )

    product_delete.is_active = False
    await db.commit()
    return {
        'status_code': status.HTTP_200_OK,
        'transaction': 'Product delete is successful'
    }