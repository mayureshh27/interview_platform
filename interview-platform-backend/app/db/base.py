# Import all the models, so that Base has them before being
# imported by Alembic
from app.db.base_class import Base
from app.models.user import User
from app.models.interview import Interview
from app.models.analysis import Analysis
# Import all models here