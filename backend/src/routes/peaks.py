from fastapi import APIRouter,Depends
from ..config.database import get_db
from ..services.auth import current_user
from ..services.peaks import published,pending,overview
router=APIRouter(prefix='/peaks')
@router.get('/published')
def get_published(db=Depends(get_db),user=Depends(current_user)):return published(db)
@router.get('/pending')
def get_pending(db=Depends(get_db),user=Depends(current_user)):return pending(db)
@router.get('/overview')
def get_overview(db=Depends(get_db),user=Depends(current_user)):return overview(db)
