from fastapi import APIRouter, UploadFile, File, HTTPException
from app.services.ics_parser import parse_ics_data

router = APIRouter()

@router.post("/parse-ics")
async def parse_ics_file(file: UploadFile = File(...)):
    # Basic extension check
    if not file.filename.lower().endswith('.ics'):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .ics files allowed.")
    
    try:
        content = await file.read()
        data = parse_ics_data(content)
        return data
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        print(f"Error parsing ICS: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse ICS file.")
