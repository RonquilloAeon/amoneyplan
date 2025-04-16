import logging
from functools import wraps
from typing import Annotated, Any, Callable, Union

import strawberry
from strawberry import relay
from strawberry.federation.schema_directives import Shareable
from strawberry.scalars import JSON
from strawberry.utils.str_converters import to_camel_case

logger = logging.getLogger("django")


@strawberry.type(directives=[Shareable()])
class EmptySuccess:
    """A successful response without any data"""

    is_message_displayable: bool
    message: str


def serialize_node(node: Any) -> Any:
    """
    Recursively serialize a node or a list of nodes to a dictionary.
    Supports both single nodes and lists of nodes.
    """
    if isinstance(node, relay.Node):
        # Serialize a single node
        node_data = {}

        for key, value in vars(node).items():
            if key == "id":
                # Convert ID to base64
                node_data["id"] = relay.to_base64(node.__class__.__name__, value)
            else:
                node_data[to_camel_case(key)] = serialize_node(value)  # Recursively serialize fields

        return node_data

    elif isinstance(node, list):
        # Serialize a list of nodes
        return [serialize_node(item) for item in node]

    # Return primitive types or objects that don't need serialization
    return node


@strawberry.type(directives=[Shareable()])
class Success:
    """A successful response with optional entities and message"""

    data: JSON

    is_message_displayable: bool = False
    message: str

    @classmethod
    def from_node(
        cls, node: relay.Node, is_message_displayable: bool = False, message: str | None = None
    ) -> "Success":
        """
        Factory method to create a Success instance from a relay Node.
        This allows for easy wrapping of any node in a Success response.
        """
        data = serialize_node(node)

        logger.info("Serialized node data for Success response type: %s", data)

        if not message:
            is_message_displayable = False

        return cls(data=data, is_message_displayable=is_message_displayable, message=message or "Ok")


@strawberry.type(directives=[Shareable()])
class ApplicationError:
    """An error that occurred during normal application flow"""

    message: str


@strawberry.type(directives=[Shareable()])
class UnexpectedError:
    """An unexpected error that occurred during execution"""

    message: str


_MutationUnion = strawberry.union(
    "MutationResponse",
    types=(ApplicationError, EmptySuccess, Success, UnexpectedError),
)

MutationResponse = Annotated[
    Union[ApplicationError, EmptySuccess, Success, UnexpectedError],
    _MutationUnion,
]


def gql_error_handler(fn: Callable) -> Callable:
    @wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> MutationResponse:
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            # Handle generic errors without leaking system details
            logger.exception(f"Unexpected error in resolver {fn.__name__}: {str(e)}", exc_info=True)
            return UnexpectedError(
                message="An unexpected error occurred. "
                "Our team will need to take a look at the problem. "
                "Please try again later."
            )

    return wrapper
