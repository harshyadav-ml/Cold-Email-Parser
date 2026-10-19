"""src.closer.input — input data loader package."""
from src.closer.input.loader import (
    DEFAULT_CONTACTS_PATH,
    DEFAULT_OPTOUT_PATH,
    SAMPLE_TEMPLATE_RECORDS,
    load_contacts,
    load_optout_list,
    parse_contacts_buffer,
    save_contacts,
    validate_contact_record,
)

__all__ = [
    "DEFAULT_CONTACTS_PATH",
    "DEFAULT_OPTOUT_PATH",
    "SAMPLE_TEMPLATE_RECORDS",
    "load_contacts",
    "load_optout_list",
    "parse_contacts_buffer",
    "save_contacts",
    "validate_contact_record",
]

