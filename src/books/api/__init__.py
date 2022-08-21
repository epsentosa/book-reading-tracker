from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine("mysql://eps:brew@0.0.0.0/track_books",future=True)
Session = sessionmaker(engine)

from books.api.routes import api
