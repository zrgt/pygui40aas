from abc import ABCMeta
from enum import Enum
from pathlib import Path

from aas.model import AssetAdministrationShell, Asset, ConceptDescription, Submodel, Property, \
    Entity, Capability, Event, Operation, RelationshipElement, AnnotatedRelationshipElement, \
    SubmodelElementCollectionUnordered, SubmodelElementCollectionOrdered, Range, Blob, File, \
    ReferenceElement, DataElement, AdministrativeInformation, Identifier, AbstractObjectStore, \
    Namespace, SubmodelElementCollection, SubmodelElement, AASReference, ConceptDictionary

import aas_editor.package
from aas_editor.settings import getCharsIcon, HIDDEN_ATTRS, CHANGED_PARENT_OBJ, ADD_ACT_AAS_TXT, \
    ADD_TYPE
from aas_editor.utils import util_classes

FILTER_AAS_FILES = """AAS files (*.aasx *.xml *.json);;
                      AASX files(*.aasx);; 
                      XML files(*.xml);;
                      JSON files(*.json);; All files (*.*)"""


LINK_TYPES = (AASReference, )

ATTR_ORDER = (
    "id_short",
    "category",
    "value",
    "in_output_variable",
    "input_variable",
    "output_variable",
    "first",
    "second",
    "kind",
    "entity_type",
    "description",
    "administration",
    "identification",
)
PREFERED_LANGS_ORDER = ("en-us", "en", "de")

CLASSES_INFO = {
    object: {
        HIDDEN_ATTRS: ("namespace_element_sets", "parent", "security")
    },
    aas_editor.package.Package: {
        HIDDEN_ATTRS: ("ATTRS_INFO", *aas_editor.package.Package.packViewAttrs()),
        ADD_ACT_AAS_TXT: "Add package",
        ADD_TYPE: aas_editor.package.Package,
    },
    AssetAdministrationShell: {
        CHANGED_PARENT_OBJ: "concept_dictionary",
        ADD_ACT_AAS_TXT: "Add concept dictionary",
        ADD_TYPE: ConceptDictionary,
    },
    Submodel: {
        HIDDEN_ATTRS: ("submodel_element",),
        CHANGED_PARENT_OBJ: "submodel_element",
        ADD_ACT_AAS_TXT: "Add submodel element",
        ADD_TYPE: SubmodelElement,
    },
    AnnotatedRelationshipElement: {
        HIDDEN_ATTRS: ("annotation",),
        CHANGED_PARENT_OBJ: "annotation",
        ADD_ACT_AAS_TXT: "Add annotation",
        ADD_TYPE: DataElement,
    },
    SubmodelElementCollection: {
        HIDDEN_ATTRS: ("value",),
        CHANGED_PARENT_OBJ: "value",
        ADD_ACT_AAS_TXT: "Add collection submodel element",
        ADD_TYPE: SubmodelElement,
    },
    Entity: {
        HIDDEN_ATTRS: ("statement",),
        CHANGED_PARENT_OBJ: "statement",
        ADD_ACT_AAS_TXT: "Add statement",
        ADD_TYPE: SubmodelElement,
    },
}


ATTR_INFOS_TO_SIMPLIFY = (AdministrativeInformation, Identifier,)
TYPES_NOT_TO_POPULATE = (
    AbstractObjectStore, str, int, float, bool, Enum, ABCMeta, Path, util_classes.DictItem)  # '+ TYPES_IN_ONE_ROW
COMPLEX_ITERABLE_TYPES = (Namespace,)
DEFAULT_ATTRS_TO_HIDE = {"parent": None}

TYPE_ICON_DICT = {
    AssetAdministrationShell: getCharsIcon("shl"),  # qta.icon("mdi.wallet") #  mdi.tab mdi.shredder folder-outline wallet
    Asset: getCharsIcon("ast"),  # qta.icon("mdi.mini-sd") # mdi.toy-brick
    ConceptDescription: getCharsIcon("cnc"),  # qta.icon("mdi.text-box")
    Submodel: getCharsIcon("sub"),

    Property: getCharsIcon("prp"),
    Entity: getCharsIcon("ent"),
    Capability: getCharsIcon("cap"),
    Event: getCharsIcon("evnt"),  # qta.icon("mdi.timeline-clock")  # mdi.timer mdi.bell
    Operation: getCharsIcon("opr"),  # qta.icon("mdi.cog")
    RelationshipElement: getCharsIcon("rel"),
    AnnotatedRelationshipElement: getCharsIcon("rel"), # qta.icon("mdi.arrow-left-right")  # mdi.relation-one-to-one
    SubmodelElementCollectionUnordered: getCharsIcon("col"),
    SubmodelElementCollectionOrdered: getCharsIcon("col"),  # qta.icon("mdi.package")

    Range: getCharsIcon("rng"),
    Blob: getCharsIcon("blb"),
    File: getCharsIcon("file"),
    ReferenceElement: getCharsIcon("ref"),
    DataElement: getCharsIcon("data"),
}
