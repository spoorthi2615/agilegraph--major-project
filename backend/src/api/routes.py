from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def get_status():
    return {"status": "ok", "message": "AgileGraph backend is running."}

@router.get("/mosca-index")
def get_mosca_readiness_index(confidentiality: int = 10, migration: int = 5, quantum: int = 20):
    """
    Mosca's Inequality: x (confidentiality) + y (migration) > z (quantum horizon)
    """
    readiness = "Vulnerable" if (confidentiality + migration > quantum) else "Safe"
    return {"readiness": readiness, "c_period": confidentiality, "m_time": migration, "q_horizon": quantum}
