from flask import Blueprint
from flask import jsonify
from sqlalchemy import select
from books.api import Session
from books.api.models import Books,Collections

api = Blueprint('api',__name__)

@api.get('/api/search/<string:title>')
def search(title):
    title = f"%{title}%"
    query = select(Books.title,Books.num_pages).where(Books.title.like(title))
    with Session() as session:
        result = session.execute(query).all()

    content = [dict(item) for item in result]

    return jsonify(content)

@api.get('/api/collections')
def collections():
    query = select(Collections.collection_id,Collections.member_id,Collections.book_id)
    with Session() as session:
        result = session.execute(query).all()

    content = [dict(item) for item in result]

    return jsonify(content)

    #TODO joining table using sqlalchemy
