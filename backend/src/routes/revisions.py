from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..schemas.revision import RevisionInput,PublishInput
from ..services.auth import current_user,writer
from ..services.revisions import listing,create,detail,publish
router=APIRouter(prefix='/revisions')
@router.get('')
def get(db=Depends(get_db),user=Depends(current_user)):return listing(db)
@router.post('',status_code=201)
def add(data:RevisionInput,db=Depends(get_db),user=Depends(writer)):return create(db,data)
@router.get('/{ident}')
def one(ident:int,db=Depends(get_db),user=Depends(current_user)):return detail(db,ident)
@router.post('/{ident}/publish')
def switch(ident:int,data:PublishInput,db=Depends(get_db),user=Depends(writer)):return publish(db,ident,data)
