from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.common import ResponseBuilder, SuccessResponse
from app.schemas.posts import (
    PostCreateRequest,
    PostResponse,
    PostUpdateRequest,
    convert_post_create_request_to_internal,
    convert_post_model_to_response,
    convert_post_update_request_to_internal,
)
from app.services.post_service import PostService
from app.utils.auth import get_current_user
from app.utils.i18n import __
from app.utils.tracing import get_trace_logger

router = APIRouter()

# Initialize logger
logger = get_trace_logger("post-controller")


@router.post(
    "/", response_model=SuccessResponse[PostResponse], status_code=status.HTTP_201_CREATED
)  # type: ignore[misc]
async def create_post(
    *, db: AsyncSession = Depends(get_db), post_in: PostCreateRequest, current_user: Any = Depends(get_current_user)
) -> SuccessResponse[PostResponse]:
    """
    Create a new post with nested relationships.

    Supports creating posts with:
    - Tags (many-to-many)
    - Comments (one-to-many)
    - Multi-level nested relationships
    """
    logger.info("Creating new post")

    post_service = PostService()

    # Convert request schema to internal schema
    internal_post_data = convert_post_create_request_to_internal(post_in, current_user.id)

    # Create post with nested relationships using internal schema
    post = await post_service.create_post_with_content(
        db=db,
        post_data=internal_post_data,
    )

    logger.info(f"Post created successfully with ID: {post.id}")

    # Convert model to response schema
    post_response = convert_post_model_to_response(post)

    return ResponseBuilder.success(message=__("general.operation_successful"), data=post_response)


@router.get("/", response_model=SuccessResponse[List[PostResponse]])  # type: ignore[misc]
async def get_posts(
    *, db: AsyncSession = Depends(get_db), skip: int = 0, limit: int = 100, search: Optional[str] = None
) -> SuccessResponse[List[PostResponse]]:
    """
    Get posts with optional search.

    Supports:
    - Pagination
    - Search by title
    - Relationship loading
    """
    logger.info(f"Retrieving posts - skip: {skip}, limit: {limit}, search: {search}")

    post_service = PostService()

    if search:
        posts = await post_service.search_posts(db=db, search_term=search, skip=skip, limit=limit)
    else:
        posts = await post_service.get_all(db=db, skip=skip, limit=limit)

    logger.info(f"Retrieved {len(posts)} posts")

    # Convert models to response schemas
    posts_response = [convert_post_model_to_response(post) for post in posts]

    return ResponseBuilder.success(message=__("general.operation_successful"), data=posts_response)


@router.get("/{post_id}", response_model=SuccessResponse[PostResponse])  # type: ignore[misc]
async def get_post(
    *, db: AsyncSession = Depends(get_db), post_id: str, include_tags: bool = True, include_comments: bool = True
) -> SuccessResponse[PostResponse]:
    """
    Get a specific post with relationships.

    Supports:
    - Loading tags (many-to-many)
    - Loading comments (one-to-many)
    - Multi-level nested relationships
    """
    logger.info(f"Retrieving post with ID: {post_id}")

    post_service = PostService()

    post = await post_service.get_post_with_relationships(
        db=db, post_id=post_id, include_tags=include_tags, include_comments=include_comments
    )

    if not post:
        logger.warning(f"Post not found with ID: {post_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=__("general.not_found"))

    logger.info(f"Post retrieved successfully: {post_id}")

    # Convert model to response schema
    post_response = convert_post_model_to_response(post)

    return ResponseBuilder.success(message=__("general.operation_successful"), data=post_response)


@router.put("/{post_id}", response_model=SuccessResponse[PostResponse])  # type: ignore[misc]
async def update_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_id: str,
    post_in: PostUpdateRequest,
    current_user: Any = Depends(get_current_user),
) -> SuccessResponse[PostResponse]:
    """
    Update a post with nested relationships and optimistic locking.

    Supports:
    - Updating post content
    - Managing tags (many-to-many)
    - Managing comments (one-to-many)
    - Optimistic locking with updated_at
    """
    logger.info(f"Updating post with ID: {post_id}")

    post_service = PostService()

    # Convert request schema to internal schema
    internal_update_data = convert_post_update_request_to_internal(post_in)

    # Update post with nested relationships using internal schema
    post = await post_service.update_post_content(
        db=db,
        post_id=post_id,
        update_data=internal_update_data,
    )

    if not post:
        logger.warning(f"Post not found for update with ID: {post_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=__("general.not_found"))

    logger.info(f"Post updated successfully: {post_id}")

    # Convert model to response schema
    post_response = convert_post_model_to_response(post)

    return ResponseBuilder.success(message=__("general.operation_successful"), data=post_response)


@router.delete("/{post_id}", response_model=SuccessResponse[None])  # type: ignore[misc]
async def delete_post(
    *,
    db: AsyncSession = Depends(get_db),
    post_id: str,
    current_user: Any = Depends(get_current_user),
    hard_delete: bool = False,
) -> SuccessResponse[None]:
    """
    Delete a post with cascade options.

    Supports:
    - Soft delete (default)
    - Hard delete with cascade
    - Relationship cleanup
    """
    logger.info(f"Deleting post with ID: {post_id}, hard_delete: {hard_delete}")

    post_service = PostService()

    # Delete post with cascade
    post = await post_service.delete(db=db, id=post_id, hard_delete=hard_delete)

    if not post:
        logger.warning(f"Post not found for deletion with ID: {post_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=__("general.not_found"))

    logger.info(f"Post deleted successfully: {post_id}")

    # Return success response for deletion (no data needed)
    return ResponseBuilder.deleted(message=__("general.operation_successful"))


@router.get("/author/{author_id}", response_model=SuccessResponse[List[PostResponse]])  # type: ignore[misc]
async def get_posts_by_author(
    *, db: AsyncSession = Depends(get_db), author_id: str, skip: int = 0, limit: int = 100
) -> SuccessResponse[List[PostResponse]]:
    """
    Get posts by a specific author.

    Supports:
    - Pagination
    - Author filtering
    - Relationship loading
    """
    logger.info(f"Retrieving posts by author: {author_id}, skip: {skip}, limit: {limit}")

    post_service = PostService()

    posts = await post_service.get_posts_by_author(db=db, author_id=author_id, skip=skip, limit=limit)

    logger.info(f"Retrieved {len(posts)} posts for author: {author_id}")

    # Convert models to response schemas
    posts_response = [convert_post_model_to_response(post) for post in posts]

    return ResponseBuilder.success(message=__("general.operation_successful"), data=posts_response)
