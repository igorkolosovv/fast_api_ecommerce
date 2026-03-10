from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from app.backend.db_depends import get_db
from slugify import slugify

from sqlalchemy import insert, select, update

from fastapi import APIRouter, Depends, status, HTTPException

from app.models.category import Category
from app.models.products import Product
from app.schemas import CreateProduct

from app.routers.auth import get_current_user

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
async def create_product(db: Annotated[AsyncSession, Depends(get_db)], product_data: CreateProduct, get_user: Annotated[dict, Depends(get_current_user)]):
    if get_user.get('is_admin') or get_user.get('is_supplier'):
        await db.execute(insert(Product).values(
            name=product_data.name,
            slug=slugify(product_data.name),
            description=product_data.description,
            price=product_data.price,
            image_url=product_data.image_url,
            stock=product_data.stock,
            category_id=product_data.category,
            rating=0.0,
            supplier_id=get_user.get('id')
        ))
        await db.commit()
        return {
            'status_code': status.HTTP_201_CREATED,
            'transaction': 'Successful'
        }
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="You are not authorized to use this method"
        )


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
        update_product_model: CreateProduct,
        get_user: Annotated[dict, Depends(get_current_user)]
):

    product_update = await db.scalar(select(Product).where(Product.slug == product_slug))
    if not product_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="There is no product found"
        )
    if get_user.get('id') == product_update.supplier_id or get_user.get('is_admin'):
        if get_user.get('id') == product_update.supplier_id or get_user.get('is_admin'):
            await db.execute(
                update(Product).where(Product.slug == product_slug)
                .values(name=update_product_model.name,
                        description=update_product_model.description,
                        price=update_product_model.price,
                        image_url=update_product_model.image_url,
                        stock=update_product_model.stock,
                        category_id=update_product_model.category,
                        slug=slugify(update_product_model.name)))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'transaction': 'Product update is successful'
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='You are not authorized to use this method'
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )


@router.delete('/delete')
async def delete_product(db: Annotated[AsyncSession, Depends(get_db)], product_id: int,
                         get_user: Annotated[dict, Depends(get_current_user)]):
    product_delete = await db.scalar(select(Product).where(Product.id == product_id))
    if product_delete is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='There is no product found'
        )
    if get_user.get('is_supplier') or get_user.get('is_admin'):
        if get_user.get('id') == product_delete.supplier_id or get_user.get('is_admin'):
            await db.execute(update(Product).where(Product.id == product_id).values(is_active=False))
            await db.commit()
            return {
                'status_code': status.HTTP_200_OK,
                'transaction': 'Product delete is successful'
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail='You are not authorized to use this method'
            )
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='You are not authorized to use this method'
        )