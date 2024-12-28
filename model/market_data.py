# 引入包不取別名，大家協作時就可以少翻上來參考，雖然字母多一點，但還是可以忍受的

from decimal import Decimal
from pydantic import BaseModel, ConfigDict, Field
from pydantic_settings import BaseSettings
from fastapi.encoders import jsonable_encoder
from zoneinfo import ZoneInfo

import tzdata
import numpy

