from flask import Blueprint
from flask import jsonify
from sqlalchemy import select
from sqlalchemy import and_
from sqlalchemy import func
from sqlalchemy.orm import aliased
from books.api import Session
from books.api.models import Authors
from books.api.models import Books
from books.api.models import Collections
from books.api.models import Members
from books.api.models import Notes
from books.api.models import Publishers

api = Blueprint('api',__name__)

@api.get('/api/search/<string:title>')
def search(title):
    title = f"%{title}%"
    query = select(Books.title,Books.num_pages).where(Books.title.like(title))
    with Session() as session:
        result = session.execute(query).all()

    content = [dict(item) for item in result]

    return jsonify(content)

@api.get('/api/collections/<int:member_id>')
def collections(member_id):
    # search_query = """ SELECT b.book_id,b.title,b.num_pages,b.publication_date,b.isbn, 
    #                 p.name,a.name,m_add.full_name,COUNT(n.book_id) FROM books b
    #                 LEFT JOIN publishers p ON b.publisher_id = p.publisher_id 
    #                 LEFT JOIN authors a ON b.author_id = a.author_id 
    #                 LEFT JOIN members m_add ON b.added_by = m_add.member_id
    #                 INNER JOIN collections c ON c.book_id = b.book_id
    #                 INNER JOIN members m ON c.member_id = m.member_id
    #                 LEFT JOIN notes n ON m.member_id = n.member_id AND b.book_id = n.book_id
    #                 where c.member_id = %s and b.title LIKE '%%%s%%' 
    #                 GROUP BY book_id """ % (member_id,title)
    added_by = aliased(Members)
    query = select(Books.book_id,Books.title,Books.num_pages,Books.publication_date,Books.isbn,
                    Publishers.name,Authors.name,added_by.full_name,func.COUNT(Notes.book_id)).\
            join(Publishers,Books.publisher_id == Publishers.publisher_id,isouter=True).\
            join(Authors,Books.author_id == Authors.author_id,isouter=True).\
            join(added_by,Books.added_by == added_by.member_id,isouter=True).\
            join(Collections,Collections.book_id == Books.book_id).\
            join(Members,Collections.member_id == Members.member_id).\
            join(Notes,and_(Members.member_id == Notes.member_id, Books.book_id == Notes.book_id)
                ,isouter=True).\
            where(Collections.member_id==member_id).group_by(Books.book_id).order_by(Books.book_id)
    with Session() as session:
        result = session.execute(query).all()

    content = [dict(item) for item in result]
    print(len(content))

    return jsonify(content)

    #TODO figure how to rename aliases and result automatically in jsonify
