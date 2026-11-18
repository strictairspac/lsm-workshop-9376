from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..schemas.config import ConfigInput
from ..services.auth import current_user,writer
from ..services.config import listing,create
router=APIRouter(prefix='/configs')
@router.get('')
def get(db=Depends(get_db),user=Depends(current_user)):return listing(db)
@router.post('',status_code=201)
def add(data:ConfigInput,db=Depends(get_db),user=Depends(writer)):return create(db,data)
