from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    email = Column(String)

class Book(Base):
    __tablename__ = 'book'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    author = Column(String)
    genre = Column(String)
    user_id = Column(Integer, ForeignKey(User.id))
    user = relationship(User)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id' : self.id,
            'title' : self.title,
            'description' : self.description,
            'author' : self.author,
            'genre' : self.genre
        }


engine = create_engine('postgresql://postgres:udacity@localhost/catalog')

Base.metadata.create_all(engine)
