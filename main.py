from datetime import datetime, timezone 
from typing import Optional
from uuid import uuid4
from fastapi import Depends, FastAPI, HTTPException, Header, Request
from pydantic import BaseModel, Field
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

bearer_scheme = HTTPBearer()

app = FastAPI(title="Content Feed API")


# In memory storage
posts_ordered = [] # for post_ids sorted
replies={}
upvotes={}
posts={}




class AuthRequest(BaseModel):
    userId: str

class CreatePostRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)

class ReplyRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=500)

class PostResponse(BaseModel):
    id: str
    text: str
    authorId: str
    createdAt: str
    upvoteCount: str
    replyCount: int

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def get_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
):
    token = credentials.credentials
    scheme = credentials.scheme

    print("SCHEME:", scheme)
    print("TOKEN:", token)

    if scheme != "Bearer" or not token.startswith("Bearer mock-"):
        raise HTTPException(status_code=401, detail="Unauthorized")

    return token.replace("mock-", "")


@app.post("/auth/mock")
def mock_authentication(payload: AuthRequest):
    return {"token": f"mock-{payload.userId}"}


@app.post("/post", response_model=PostResponse)
def create_post(payload: CreatePostRequest, user_id: str = Depends(get_user)):
    post_id = f"p_{uuid4().hex[:8]}"

    post = {
        "id": post_id,
        "text": payload.text,
        "authorId": user_id,
        "createdAt": now_iso(),
        "upvoteCount": 0,
        "replyCount": 0
    }

    posts[post_id] = post   # ✅ FIXED
    posts_ordered.insert(0, post_id)
    replies[post_id] = []
    upvotes[post_id] = set()

    return post


@app.get("/feed")
def get_feed(cursor: Optional[str] = None, limit: int = 10):
    if limit > 50:
        limit = 50
    start_index = 0
    if cursor:
        start_index = posts_ordered.index(cursor) + 1
    slice_posts = posts_ordered[start_index: start_index + limit]
    items = [{
        "id": posts[p]["id"],
          "text": posts[p]["text"], 
          "createdAt": posts[p]["createdAt"],
          "upvoteCount": len(upvotes[p]),
          "replyCount": len(replies[p])
          } for p in slice_posts]
    next_cursor = slice_posts[-1] if len(slice_posts) == limit else None

    return{"items": items, "nextCursor": next_cursor}


@app.post("/post/{post_id}/replies")
def add_reply(post_id: str, body: ReplyRequest, user_id: str = Depends(get_user)):
    if post_id not in posts:
        raise HTTPException(status_code=404, detail="Not Found")
    reply = {
        "id": f"r_{uuid4().hex[:8]}",
        "postId": post_id,
        "authorId": user_id,
        "text": body.text,
        "createdAt": now_iso()
    }
    replies[post_id].append(reply)
    posts[post_id]["replyCount"] += 1
    return reply

@app.post("/posts/{post_id}/upvote")
def toggle_upvote(post_id: str, user_id: str = Depends(get_user)):
    user_set = upvotes[post_id]
    if user_id in user_set:
        user_set.remove(user_id)
        has_upvoted = False
    else:
        user_set.add(user_id)
        has_upvoted = True

    return {
        "postId": post_id,
        "upvoteCount": len(user_set),
        "hasUpvoted": has_upvoted
    }        