# pfb_backend

# How to install dependencies
- Create virtual environment
- pip install -r requirement.txt

# How to run
- Run cmd uvicorn main:app --reload

# API documentation
- http://127.0.0.1:8000/docs

# what you would use in production.
- PostgreSQL
- posts table (id, author_id, created_at)
- replies table (post_id index)
- post_upvotes table
  UNIQUE(post_id, user_id)
- Cursor pagination using (created_at, id)
- Redis cache for feed hot pages
