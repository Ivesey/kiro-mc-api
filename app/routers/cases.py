from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
import uuid

from app.models.case import CaseModel
from app.models.requests import CreateCaseRequest, UpdateCaseRequest
from app.models.errors import ErrorResponse
from app.dal.case_dal import CaseDAL
from app.dependencies import get_dal

router = APIRouter()


@router.post(
    "/",
    status_code=201,
    response_model=CaseModel,
    responses={
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Create a new support case",
    description="Creates a new support case with a generated UUID4 identifier.",
)
def create_case(body: CreateCaseRequest, dal: CaseDAL = Depends(get_dal)) -> CaseModel:
    try:
        case = CaseModel(
            case_id=uuid.uuid4(),
            email=body.email,
            issue=body.issue,
            response=body.response,
            severity=body.severity,
        )
        return dal.create_case(case)
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"detail": "Case not found"},
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)[:500]},
        )
    except TypeError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": str(e)[:500]},
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred"},
        )


@router.get(
    "/",
    response_model=list[CaseModel],
    responses={
        500: {"model": ErrorResponse},
    },
    summary="Get all support cases",
    description="Retrieves all support cases from the data store.",
)
def get_all_cases(dal: CaseDAL = Depends(get_dal)) -> list[CaseModel]:
    try:
        return dal.get_all_cases()
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred"},
        )


@router.get(
    "/{case_id}",
    response_model=CaseModel,
    responses={
        404: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Get a support case by ID",
    description="Retrieves a single support case by its UUID identifier.",
)
def get_case_by_id(case_id: uuid.UUID, dal: CaseDAL = Depends(get_dal)) -> CaseModel:
    try:
        return dal.get_case_by_id(case_id)
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Case with case_id={case_id} not found"},
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)[:500]},
        )
    except TypeError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": str(e)[:500]},
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred"},
        )


@router.put(
    "/{case_id}",
    response_model=CaseModel,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Update a support case",
    description="Replaces all fields of an existing support case.",
)
def update_case(
    case_id: uuid.UUID, body: UpdateCaseRequest, dal: CaseDAL = Depends(get_dal)
) -> CaseModel:
    try:
        case = CaseModel(
            case_id=case_id,
            email=body.email,
            issue=body.issue,
            response=body.response,
            severity=body.severity,
        )
        return dal.update_case(case_id, case)
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Case with case_id={case_id} not found"},
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)[:500]},
        )
    except TypeError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": str(e)[:500]},
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred"},
        )


@router.delete(
    "/{case_id}",
    status_code=204,
    responses={
        404: {"model": ErrorResponse},
        400: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
    summary="Delete a support case",
    description="Removes a support case from the data store.",
)
def delete_case(case_id: uuid.UUID, dal: CaseDAL = Depends(get_dal)) -> None:
    try:
        dal.delete_case(case_id)
    except KeyError:
        return JSONResponse(
            status_code=404,
            content={"detail": f"Case with case_id={case_id} not found"},
        )
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"detail": str(e)[:500]},
        )
    except TypeError as e:
        return JSONResponse(
            status_code=422,
            content={"detail": str(e)[:500]},
        )
    except Exception:
        return JSONResponse(
            status_code=500,
            content={"detail": "An internal error occurred"},
        )
