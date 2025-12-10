from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.certificate import CertificateResponse, CertificateVerification
from app.services.certificate_service import certificate_service

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("/mine", response_model=CertificateResponse)
async def get_my_certificate(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the current user's certificate.
    
    Returns:
        Certificate details including URL and metadata
        
    Raises:
        404: If certificate not found (course not completed)
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"Certificate request from user: {current_user.email} (ID: {current_user.id})")
    
    # Query all certificates to debug
    from app.models.certificate import Certificate as CertModel
    all_certs = db.query(CertModel).all()
    logger.info(f"Total certificates in database: {len(all_certs)}")
    for cert in all_certs:
        logger.info(f"  - Cert ID: {cert.certification_id}, User ID: {cert.user_id}, Student: {cert.student_name}")
    
    certificate = certificate_service.get_user_certificate(db, current_user.id)
    
    if not certificate:
        logger.warning(f"No certificate found for user {current_user.email} (ID: {current_user.id})")
        logger.warning(f"Searched for user_id: {current_user.id} (type: {type(current_user.id)})")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found. Complete the course to receive your certificate."
        )
    
    logger.info(f"Certificate found: {certificate.certification_id}")
    return certificate


@router.get("/lookup/{short_code}")
async def lookup_certificate_by_short_code(
    short_code: str,
    db: Session = Depends(get_db)
):
    """
    Look up a certificate by its short code (first 6 chars of hex part).
    Public endpoint - no authentication required.
    
    Args:
        short_code: The 6-character short code (e.g., "5A5A93")
        
    Returns:
        Dictionary with certification_id
        
    Raises:
        404: If certificate not found
    """
    certificate = certificate_service.lookup_by_short_code(db, short_code.upper())
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found. The short code may be invalid."
        )
    
    return {"certification_id": certificate.certification_id}


@router.get("/verify/{cert_id}", response_model=CertificateVerification)
async def verify_certificate(
    cert_id: str,
    db: Session = Depends(get_db)
):
    """
    Verify a certificate by its certification ID.
    Public endpoint - no authentication required.
    
    Args:
        cert_id: The certification ID to verify
        
    Returns:
        Certificate verification information
        
    Raises:
        404: If certificate not found
    """
    certificate = certificate_service.verify_certificate(db, cert_id)
    
    if not certificate:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate not found. The certification ID may be invalid."
        )
    
    return CertificateVerification(
        certification_id=certificate.certification_id,
        student_name=certificate.student_name,
        course_title=certificate.course_title,
        issued_at=certificate.issued_at,
        is_valid=True
    )
