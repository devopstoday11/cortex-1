# Copyright 2020 Cortex Labs, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from typing import List

from cortex.lib.storage import S3, LocalStorage
from cortex.lib.log import cx_logger
from cortex.lib.model import ModelsTree
from cortex.lib.api import (
    PythonPredictorType,
    TensorFlowPredictorType,
    ONNXPredictorType,
    PredictorType,
)

import collections


class TemplatePlaceholder(collections.namedtuple("TemplatePlaceholder", "placeholder")):
    """
    Placeholder type that denotes an operation, a text placeholder, etc.
    """

    def __new__(cls, placeholder):
        return super(cls, TemplatePlaceholder).__new__(cls, "<" + placeholder + ">")

    def __str__(self) -> str:
        return str(self.placeholder)

    def __repr__(self) -> str:
        return str(self.placeholder)

    @property
    def type(self) -> str:
        return str(self.placeholder).strip("<>")


class GenericPlaceholder(collections.namedtuple("GenericPlaceholder", "placeholder value")):
    """
    Generic placeholder.

    Can hold any value.
    Can be of one type only: generic.
    """

    def __new__(cls, value):
        return super(cls, GenericPlaceholder).__new__(cls, "<generic>", value)

    def __eq__(self, other) -> bool:
        if isinstance(other, GenericPlaceholder):
            return self.placeholder == other.placeholder
        return False

    def __hash__(self):
        return hash((self.placeholder, self.value))

    def __str__(self) -> str:
        return str(self.value)

    def __repr__(self) -> str:
        return str(self.value)

    @property
    def type(self) -> str:
        return str(self.placeholder).strip("<>")


class PlaceholderGroup:
    """
    Order-based addition of placeholder types (Groups, Generics or Templates).
    """

    def __init__(self, *args):
        self.parts = args

    def __getitem__(self, index: int):
        return self.parts[index]

    def __len__(self) -> int:
        return len(self.parts)

    def __str__(self) -> str:
        return str(self.parts)

    def __repr__(self) -> str:
        return str(self.parts)


IntegerPlaceholder = TemplatePlaceholder("integer")  # the path name must be an integer
AnyPlaceholder = TemplatePlaceholder(
    "any"
)  # the path can be any file or any directory (with multiple subdirectories)
SinglePlaceholder = TemplatePlaceholder(
    "single"
)  # can only have a single occurrence of this, but its name can take any form
ExclAlternativePlaceholder = TemplatePlaceholder(
    "exclusive"
)  # can either be this template xor anything else at the same level
UniquePlaceholder = TemplatePlaceholder(
    "unique"
)  # like AnyPlaceholder, but cannot have subfolders (means that it's either a file or a directory)


# to be used when predictor:model_path or predictor:models:paths is used
model_template = {
    PythonPredictorType: {IntegerPlaceholder: AnyPlaceholder},
    TensorFlowPredictorType: {
        IntegerPlaceholder: {
            AnyPlaceholder: None,
            GenericPlaceholder("saved_model.pb"): None,
            GenericPlaceholder("variables"): {
                GenericPlaceholder("variables.index"),
                PlaceholderGroup(GenericPlaceholder("variables.data-00000-of-"), AnyPlaceholder),
                AnyPlaceholder,
            },
        },
    },
    ONNXPredictorType: {
        IntegerPlaceholder: {PlaceholderGroup(SinglePlaceholder, GenericPlaceholder(".onnx")),},
        PlaceholderGroup(
            ExclAlternativePlaceholder, SinglePlaceholder, GenericPlaceholder(".onnx")
        ): None,
    },
}

# to be used when predictor:models:dir is used
def dirs_model_pattern(predictor_type: PredictorType) -> dict:
    return {UniquePlaceholder: model_template[predictor_type]}


# to be used when predictor:model_path or predictor:models:paths is used
def model_pattern(predictor_type: PredictorType) -> dict:
    return model_template[predictor_type]


# to be used when predictor:models:dir is used
def models_tree_from_s3_top_paths(s3_top_paths: List[str], predictor_type: PredictorType) -> dict:
    for s3_top_path in s3_top_paths:
        model_name = os.path.dirname(s3_top_path)
    return {}


# to be used when predictor:model_path or predictor:models:paths is used
def models_tree_from_s3_path(s3_path: List[str], predictor_type: PredictorType) -> dict:
    return {}