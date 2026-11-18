from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..schemas.dataset import DatasetInput
from ..services.auth import current_user,writer
from ..services.dataset import listing,create
router=APIRouter(prefix='/datasets')
@router.get('')
def get(db=Depends(get_db),user=Depends(current_user)):return listing(db)
@router.post('',status_code=201)
def add(data:DatasetInput,db=Depends(get_db),user=Depends(writer)):return create(db,data)
