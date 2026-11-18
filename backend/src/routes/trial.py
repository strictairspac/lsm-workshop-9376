import json
from fastapi import APIRouter,Depends,Response
from ..config.database import get_db
from ..schemas.trial import TrialInput
from ..services.auth import current_user,writer
from ..services.trial import listing,create,detail
router=APIRouter(prefix='/trials')
@router.get('')
def get(db=Depends(get_db),user=Depends(current_user)):return listing(db)
@router.post('',status_code=202)
def add(data:TrialInput,db=Depends(get_db),user=Depends(writer)):return create(db,data)
@router.get('/{ident}')
def one(ident:int,db=Depends(get_db),user=Depends(current_user)):return detail(db,ident)
@router.get('/{ident}/export')
def export(ident:int,db=Depends(get_db),user=Depends(current_user)):
    return Response(json.dumps(detail(db,ident),ensure_ascii=False,indent=2),media_type='application/json',headers={'Content-Disposition':f'attachment; filename="lsm-trial-{ident}.json"'})
