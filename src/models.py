
import uuid
import datetime
import jsonschema
import ipaddress
import jsonpatch
import json

from sqlalchemy.orm import validates, Session, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, String, Boolean, DateTime, Text, JSON, event, inspect, ForeignKey
from sqlalchemy.ext.hybrid import hybrid_property

from db import db

Base = db.Model

# JSON Schema for form_parts validation
form_parts_schema = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "input_name": {"type": "string"},
            "input_type": {"type": "string"},
            "input_rect": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "items": {
                    "type": "array",
                    "minItems": 2,
                    "maxItems": 2,
                    "items": {"type": "number"},
                },
            }
        },
        "required": ["input_rect", "input_name", "input_type"],
    },
}

class CharSheetType(Base):
    __tablename__ = 'charsheet_type'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Text, nullable=False, unique=True)
    form_parts = Column(JSON, nullable=False)
    b64_img = Column(Text, nullable=False)  # Base64-encoded PNG image

    instances = relationship('CharSheetInstance', backref='sheet_type', lazy='dynamic')

    @validates('name')
    def validate_name(self, key, name):
        assert name.strip(), "Name must not be empty or whitespace only."
        return name

    @validates('form_parts')
    def validate_form_parts(self, key, form_parts):
        jsonschema.validate(instance=form_parts, schema=form_parts_schema)
        return form_parts


class CharSheetInstance(Base):
    __tablename__ = 'charsheet_instance'
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(Text, nullable=False, unique=True)
    sheet_type_id = Column(String(36), ForeignKey('charsheet_type.id'), nullable=False)
    form_values = Column(JSON)
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.utcnow)
    creation_ip = Column(Text, nullable=False)
    deleted = Column(Boolean, nullable=False, default=False)

    revisions = relationship('CharSheetRevisions', backref='charsheet_instance', lazy='dynamic')
    
    @validates('name')
    def validate_name(self, key, name):
        assert name.strip(), "Name must not be empty or whitespace only."
        return name

    @validates('creation_ip')
    def validate_creation_ip(self, key, creation_ip):
        try:
            ip = ipaddress.ip_address(creation_ip)
            return str(ip)
        except ValueError:
            raise AssertionError("Invalid IP address format.")


class CharSheetRevisions(Base):
    __tablename__ = 'charsheet_revisions'
    
    rev_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    csinst_id = Column(String(36), ForeignKey('charsheet_instance.id'), nullable=False)
    revision_dttm = Column(DateTime, nullable=False, default=lambda _: datetime.datetime.now(tz=datetime.timezone.utc))
    form_diff = Column(JSON, nullable=False)

    def __init__(self, csinst_id, form_diff):
        self.csinst_id = csinst_id
        self.form_diff = form_diff

    @hybrid_property
    def form_values(self):
        # Create a new session to query previous revisions
        session = Session.object_session(self)
        if session is None:
            raise RuntimeError("Session is not bound to an engine or context")

        # Fetch all previous revisions ordered by revision_dttm
        previous_revisions = (
            session.query(CharSheetRevisions)
            .filter(
                CharSheetRevisions.csinst_id == self.csinst_id,
                CharSheetRevisions.revision_dttm <= self.revision_dttm
            )
            .order_by(CharSheetRevisions.revision_dttm)
            .all()
        )

        # Combine all form_diff patches in sequence
        base_form = {}
        for revision in previous_revisions:
            patch = jsonpatch.JsonPatch(revision.form_diff)
            if patch:
                base_form = jsonpatch.apply_patch(base_form, patch)
        
        return base_form

@event.listens_for(CharSheetInstance, 'after_insert')
def receive_after_insert(mapper, connection, target):
    session = Session(bind=connection)
    # Creating a diff from an empty object to the initial form_values
    initial_diff = jsonpatch.make_patch({}, target.form_values or {}).patch
    revision = CharSheetRevisions(csinst_id=target.id, form_diff=initial_diff)
    session.add(revision)
    session.commit()
    
@event.listens_for(CharSheetInstance, 'before_update')
def receive_before_update(mapper, connection, target):
    """
    Before updating a CharSheetInstance row, query the old `form_values` record for the target instance ID,
    and compute a diff between the old and new values.
    """

    session = Session(bind=connection)

    # Inspect the target to access change history for `form_values`
    state = inspect(target)
    history = state.get_history('form_values', True)

    # Fetch old and new values for diffing
    old_value = history.deleted[0] if history.deleted and history.deleted[0] else {}
    new_value = history.added[0] if history.added else {}

    # Compute the diff between old and new form values
    patch = jsonpatch.make_patch(old_value, new_value).patch

    # If there is a difference, create a new revision
    if patch:
        revision = CharSheetRevisions(csinst_id=target.id, form_diff=patch)
        session.add(revision)
        session.commit()
