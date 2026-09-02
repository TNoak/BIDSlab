#  Copyright (c) 2025 by Lukas Behammer
#  University of Augsburg
#  Department of Computer Science
#  Chair of Informatics for Medical Technology
#
#  SPDX-License-Identifier: BSD-3-Clause

from typing import TYPE_CHECKING, Any, Iterable, Mapping, Sequence
from warnings import warn

from bidslab.common.specs_misc import Column
from bidslab.settings import get_settings_value
from bidslab.utils.checks import check_if_valid_uri
from bidslab.utils.exceptions import TopLevelEntityNotLinkedWarning

if TYPE_CHECKING:
    from bidslab.common.specs_summary import Participant


class PhenotypeColumn(Column):
    def __init__(
        self, name: str, **kwargs: bool | str | int | float | Mapping | Iterable
    ) -> None:
        derivative = kwargs.pop("derivative", None)
        match derivative:
            case bool() | None:
                pass
            case "true":
                derivative = True
            case "false":
                derivative = False
            case _:
                raise ValueError(
                    f"PhenotypeColumn 'derivative' field must be of type bool or None, "
                    f"got {type(derivative)}"
                )
        super().__init__(name=name, **kwargs)
        self.derivative: bool | None = derivative


class MeasurementTool:
    def __init__(self, name: str, **kwargs: Any) -> None:
        self.name: str = name
        self.description: str | None = None
        self.term_url: str | None = None

        self._participant: "Participant | None" = None

        self.columns: Sequence[PhenotypeColumn] | None = None

        for key, value in kwargs.items():
            setattr(self, key, value)

        if self.term_url and not get_settings_value("OVERRIDE_VALIDATION"):
            check_if_valid_uri(self.term_url)

    def __repr__(self) -> str:
        return f"<MeasurementTool name={self.name}>"

    @property
    def participant(self) -> "Participant | None":
        if self._participant:
            return self._participant

        warn("Participant is not linked to a Dataset", TopLevelEntityNotLinkedWarning)
        return self._participant

    @participant.setter
    def participant(self, value: "Participant") -> None:
        self._participant = value
