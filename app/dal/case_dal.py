import abc
import uuid

from app.models.case import CaseModel


class CaseDAL(abc.ABC):
    """Abstract base class defining the contract for case data access."""

    @abc.abstractmethod
    def create_case(self, case: CaseModel) -> CaseModel:
        """Persist a new case to the store.

        Args:
            case: A valid CaseModel instance to persist.

        Returns:
            The persisted CaseModel (field values identical to input).

        Raises:
            ValueError: If a case with the same case_id already exists.
        """
        ...

    @abc.abstractmethod
    def update_case(self, case_id: uuid.UUID, case: CaseModel) -> CaseModel:
        """Replace an existing case in the store.

        Args:
            case_id: UUID of the case to update.
            case: The new CaseModel data to store.

        Returns:
            The updated CaseModel (field values identical to input).

        Raises:
            KeyError: If no case with the given case_id exists.
            ValueError: If case_id is None/invalid or case is None.
        """
        ...

    @abc.abstractmethod
    def delete_case(self, case_id: uuid.UUID) -> None:
        """Remove a case from the store.

        Args:
            case_id: UUID of the case to delete.

        Raises:
            KeyError: If no case with the given case_id exists.
            ValueError: If case_id is None or not a valid UUID.
        """
        ...

    @abc.abstractmethod
    def get_all_cases(self) -> list[CaseModel]:
        """Retrieve all cases from the store.

        Returns:
            A list of all CaseModel instances. Empty list if store is empty.
        """
        ...

    @abc.abstractmethod
    def get_case_by_id(self, case_id: uuid.UUID) -> CaseModel:
        """Retrieve a single case by its identifier.

        Args:
            case_id: UUID of the case to retrieve.

        Returns:
            The matching CaseModel instance.

        Raises:
            KeyError: If no case with the given case_id exists.
            TypeError: If case_id is None or not a valid uuid.UUID.
        """
        ...
