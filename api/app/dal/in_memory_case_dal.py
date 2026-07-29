import uuid

from app.models.case import CaseModel
from app.dal.case_dal import CaseDAL


class InMemoryCaseDAL(CaseDAL):
    """In-memory implementation of CaseDAL backed by a dictionary.

    Intended for unit/property testing. Not suitable for production use.
    """

    def __init__(self) -> None:
        self._store: dict[uuid.UUID, CaseModel] = {}

    def create_case(self, case: CaseModel) -> CaseModel:
        if case.case_id in self._store:
            raise ValueError(f"Case with case_id={case.case_id} already exists")
        self._store[case.case_id] = case
        return case

    def update_case(self, case_id: uuid.UUID, case: CaseModel) -> CaseModel:
        if case_id is None:
            raise ValueError("case_id must not be None")
        if case is None:
            raise ValueError("case must not be None")
        if not isinstance(case_id, uuid.UUID):
            raise ValueError(f"case_id must be a valid uuid.UUID, got {type(case_id)}")
        if case_id not in self._store:
            raise KeyError(case_id)
        self._store[case_id] = case
        return case

    def delete_case(self, case_id: uuid.UUID) -> None:
        if case_id is None or not isinstance(case_id, uuid.UUID):
            raise ValueError("case_id must be a valid uuid.UUID")
        if case_id not in self._store:
            raise KeyError(case_id)
        del self._store[case_id]

    def get_all_cases(self) -> list[CaseModel]:
        return list(self._store.values())

    def get_case_by_id(self, case_id: uuid.UUID) -> CaseModel:
        if case_id is None or not isinstance(case_id, uuid.UUID):
            raise TypeError(f"case_id must be a uuid.UUID, got {type(case_id)}")
        if case_id not in self._store:
            raise KeyError(case_id)
        return self._store[case_id]
