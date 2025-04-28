import sqlalchemy 
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

# Define the database URL
DATABASE_URL = "sqlite:///database.db"

# Create the database engine
engine = create_engine(DATABASE_URL, echo=True)

# Define the base class for models
Base = declarative_base()

# Define an Enum for Dessert Types
class DessertType(enum.Enum):
    WHOLE_CAKES = "Whole Cakes"
    CAKE_SLICES = "Cake Slices"
    MATCHA = "Matcha"
    DESSERT_BOX = "Dessert Box"
    BEVERAGE = "Beverage"

# Define the Users table
class User(Base):
    __tablename__ = 'Users'
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, nullable=False, unique=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    profile_image = Column(String)  # Path or URL to the profile picture
    location = Column(String)
    role = Column(String, nullable=False, default="Buyer")  # Role: "Administrator" or "Buyer"

    # Relationships
    desserts = relationship("Dessert", back_populates="user")
    messages_sent = relationship("Message", foreign_keys="Message.sender_id", back_populates="sender")
    messages_received = relationship("Message", foreign_keys="Message.receiver_id", back_populates="receiver")
    reviews = relationship("Review", foreign_keys="Review.user_id", back_populates="user")
    orders = relationship("Order", back_populates="user")

# Define the Dessert table
class Dessert(Base):
    __tablename__ = 'Dessert'
    dessert_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    Name = Column(String, nullable=False)
    Type = Column(Enum(DessertType), nullable=False)  # Use Enum for predefined types
    Price = Column(String, nullable=False)
    availability = Column(String, nullable=False)
    dessert_image = Column(String)  # Path or URL to the dessert picture

    # Relationships
    user = relationship("User", back_populates="desserts")

# Define the Orders table
class Order(Base):
    __tablename__ = 'Orders'
    order_id = Column(Integer, primary_key=True)  # Remove autoincrement to allow manual assignment
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    dessert_id = Column(Integer, ForeignKey('Dessert.dessert_id'))
    order_date = Column(String, nullable=False)
    status = Column(String, nullable=False)

    # Relationships
    user = relationship("User", back_populates="orders")
    dessert = relationship("Dessert")
    order_details = relationship("OrderDetails", back_populates="order", cascade="all, delete-orphan")

# Define the OrderDetails table
class OrderDetails(Base):
    __tablename__ = 'OrderDetails'
    detail_id = Column(Integer, primary_key=True, autoincrement=True)  # Primary key for the table
    order_id = Column(Integer, ForeignKey('Orders.order_id'), nullable=False)
    dessert_id = Column(Integer, ForeignKey('Dessert.dessert_id'), nullable=False)
    quantity = Column(Integer, nullable=False)

    # Relationships
    order = relationship("Order", back_populates="order_details")
    dessert = relationship("Dessert")

# Define the Messages table
class Message(Base):
    __tablename__ = 'Messages'
    message_id = Column(Integer, primary_key=True, autoincrement=True)
    sender_id = Column(Integer, ForeignKey('Users.user_id'), nullable=False)
    receiver_id = Column(Integer, ForeignKey('Users.user_id'), nullable=False)
    content = Column(Text, nullable=False)
    timestamp = Column(String, nullable=False)

    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], back_populates="messages_sent")
    receiver = relationship("User", foreign_keys=[receiver_id], back_populates="messages_received")

# Define the Reviews table
class Review(Base):
    __tablename__ = 'Reviews'
    review_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('Users.user_id'))
    reviewer_id = Column(Integer, ForeignKey('Users.user_id'))
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    timestamp = Column(String, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="reviews")

# Create all tables in the database
Base.metadata.create_all(engine)

print("Database recreated successfully!")