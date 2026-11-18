from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..schemas.settlement import SettlementInput
from ..services.auth import current_user,writer
from ..services.settlements import listing,create,detail
router=APIRouter(prefix='/settlements')
@router.get('')
def get(db=Depends(get_db),user=Depends(current_user)):return listing(db)
@router.post('',status_code=202)
def add(data:SettlementInput,db=Depends(get_db),user=Depends(writer)):return create(db,data)
@router.get('/{ident}')
def one(ident:int,db=Depends(get_db),user=Depends(current_user)):return detail(db,ident)
