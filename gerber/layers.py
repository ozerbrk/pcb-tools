#! /usr/bin/env python
# -*- coding: utf-8 -*-

# copyright 2014 Hamilton Kibbe <ham@hamiltonkib.be>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at

#     http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
import re
from collections import namedtuple

from . import common
from .excellon import ExcellonFile
from .ipc356 import IPCNetlist
from dataclasses import dataclass
from typing import List


@dataclass
class Hint:
    layer: str
    ext: List[str]
    keywords: List[str]

hints = [
    Hint(layer='bottomsilk',
         ext=['gbo', 'ssb', 'pls', 'bs', 'skb', 'bottomsilk'],
         keywords=['bottomsilk', 'bsilk', 'silkscreen','botsilk', 'b.silks', 'bottom_silk', 'b_silk', 'silkscreen_bottom', 'bottom', 'gbo', 'ssb', 'pls', 'bs', 'skb', 'bottomsilk']),
    Hint(layer='topsilk',
         ext=['gto', 'sst', 'plc', 'ts', 'skt', 'topsilk'],
         keywords=['topsilk', 'sst01', 'silk', 'silkscreen', 'slk', 'f.silks', 'top_silk', 'f_silk', 'silkscreen_top', 'top', 'gto', 'sst', 'plc', 'ts', 'skt', 'topsilk']),
    Hint(layer='topmask',
         ext=['gts', 'stc', 'tmk', 'smt', 'tr', 'topmask'],
         keywords=['topmask', 'sm01', 'cmask', 'tmask', 'mask1', 'maskcom', 'mst', 'f.mask', 'soldermask_top', 'top_mask', 'smdmask_top', 'top', 'gts', 'stc', 'tmk', 'smt', 'tr', 'topmask']),
    Hint(layer='bottommask',
         ext=['gbs', 'sts', 'bmk', 'smb', 'br', 'bottommask'],
         keywords=['bottommask', 'sm', 'bmask', 'mask2', 'masksold', 'botmask', 'msb', 'b.mask', 'soldermask_bottom', 'bottom_mask', 'smdmask_bottom', 'bottom', 'gbs', 'sts', 'bmk', 'smb', 'br', 'bottommask']),
    Hint(layer='internal',
         ext=['in', 'gt1', 'gt2', 'gt3', 'gt4', 'gt5', 'gt6', 'g1', 'g2', 'g3', 'g4', 'g5', 'g6'],
         keywords=['internal', 'in1.cu', 'in2.cu', 'in3.cu', 'in4.cu', 'inner1', 'inner2', 'inner3', 'inner4', 'inner5', 'inner6', 'copper_inner', 'in', 'gt1', 'gt2', 'gt3', 'gt4', 'gt5', 'gt6', 'g1', 'g2', 'g3', 'g4', 'g5', 'g6']),
    Hint(layer='bottom',
         ext=['gbl', 'sld', 'bot', 'sol', 'bottom'],
         keywords=['bottom', 'bot', 'b.cu', 'layer2', 'copper_bottom', 'gbl', 'sld', 'bot', 'sol', 'bottom']),
    Hint(layer='top',
         ext=['gtl', 'cmp', 'top'],
         keywords=['top', 'f.cu', 'layer1', 'copper_top', 'gtl', 'cmp', 'top']),
    Hint(layer='outline',
         ext=['gko', 'outline'],
         keywords=['outline', 'edge.cuts', 'border', 'bdr', 'gko', 'outline', 'routing', 'cevre']),
    Hint(layer='toppaste',
         ext=['gtp', 'tm', 'toppaste'],
         keywords=['toppaste', 'sp01', 'pst', 'f.paste', 'gtp', 'tm', 'toppaste']),
    Hint(layer='bottompaste',
         ext=['gbp', 'bm', 'bottompaste'],
         keywords=['bottompaste', 'sp02', 'botpaste', 'psb', 'b.paste', 'gbp', 'bm', 'bottompaste']),
    Hint(layer='drill',
         ext=['drl', 'drill'],
         keywords=['drl', 'drill']),
    Hint(layer='ipc_netlist',
         ext=['ipc'],
         keywords=[]),
    Hint(layer='drawing',
         ext=['fab'],
         keywords=['assembly drawing', 'assembly', 'fabrication', 'fab drawing', 'fab']),
    # ... other hints ...
]
    # re.compile(r'(\.GTL|gtl|top.*copper|copper.*top|F_Cu)', re.IGNORECASE): 'top_copper',
  #   re.compile(r'(\.GBL|gbl|bottom.*copper|copper.*bottom|B_Cu)', re.IGNORECASE): 'bottom_copper',
   #   re.compile(r'(\.GTS|gts|top_mask|top.*mask|mask.*top|F_Mask)', re.IGNORECASE): 'top_mask',
   # re.compile(r'(\.GBS|gbs|bottom_mask|bottom.*mask|mask.*bottom|B_Mask)', re.IGNORECASE): 'bottom_mask',
    #  re.compile(r'(\.GTO|gto|top_silk|top.*silk|silk.*top|F_Silk)', re.IGNORECASE): 'top_silk',
    #   re.compile(r'(\.GBO|gbo|bottom_silk|bottom.*silk|silk.*bottom|B_Silk)', re.IGNORECASE): 'bottom_silk',
    #  re.compile(r'(\.DRL|drl|drill)', re.IGNORECASE): 'drill',
    #   re.compile(r'(\.GKO|gko|outline)', re.IGNORECASE): 'outline'


def load_layer(filename):
    return PCBLayer.from_cam(common.read(filename))


def load_layer_data(data, filename=None):
    return PCBLayer.from_cam(common.loads(data, filename))

def guess_layer_class(filename):
    try:
        print(f"Processing file: {filename}")
        directory, filename_only = os.path.split(filename)
        name, ext = os.path.splitext(filename_only.lower())
        ext = ext[1:]  # Remove the dot from the extension

        name_ext = f"{name}.{ext}"
        print(f"Filename without path: {filename_only}")
        print(f"Name: {name}, Extension: {ext}")

        # First, check for extension matches
        for hint in hints:
            if hasattr(hint, 'ext') and ext in hint.ext:
                print(f"Matched by extension '{ext}' with layer '{hint.layer}'")
                return hint.layer

        # If no extension match, proceed to search for keywords
        max_score = 0
        selected_layer = 'unknown'

        for hint in hints:
            score = 0
            for keyword in hint.keywords:
                if keyword.lower() in name_ext:
                    # Assign higher score for longer keywords
                    keyword_score = len(keyword)
                    score += keyword_score
                    print(f"Keyword '{keyword}' matched in '{name_ext}' for layer '{hint.layer}' with score {keyword_score}")

            if score > max_score:
                max_score = score
                selected_layer = hint.layer
            elif score == max_score and score > 0:
                pass  # Tie-breaker logic can be implemented here if needed

        if selected_layer != 'unknown':
            print(f"Selected layer '{selected_layer}' with score {max_score}")
        else:
            print("No matching layer found based on keywords.")
        return selected_layer

    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return 'unknown'



def guess_layer_class_by_content(filename):
    try:
        file = open(filename, 'r')
        for line in file:
            for hint in hints:
                if len(hint.content) > 0:
                    patterns = [r'^(.*){}(.*)$'.format(x) for x in hint.content]
                    if any(re.findall(p, line, re.IGNORECASE) for p in patterns):
                        print(f"Matched:  {filename} for layer {hint.layer}")
                        return hint.layer
    except:
        pass

    return False


def sort_layers(layers, from_top=True):
    layer_order = ['outline', 'toppaste', 'topsilk', 'topmask', 'top',
                   'internal', 'bottom', 'bottommask', 'bottomsilk',
                   'bottompaste']
    append_after = ['drill', 'drawing']

    output = []
    drill_layers = [layer for layer in layers if layer.layer_class == 'drill']
    internal_layers = list(sorted([layer for layer in layers
                                   if layer.layer_class == 'internal']))

    for layer_class in layer_order:
        if layer_class == 'internal':
            output += internal_layers
        elif layer_class == 'drill':
            output += drill_layers
        else:
            for layer in layers:
                if layer.layer_class == layer_class:
                    output.append(layer)
    if not from_top:
        output = list(reversed(output))

    for layer_class in append_after:
        for layer in layers:
            if layer.layer_class == layer_class:
                output.append(layer)
    return output


class PCBLayer(object):
    """ Base class for PCB Layers

    Parameters
    ----------
    source : CAMFile
        CAMFile representing the layer


    Attributes
    ----------
    filename : string
        Source Filename

    """
    @classmethod
    def from_cam(cls, camfile):
        filename = camfile.filename
        layer_class = guess_layer_class(filename)
        if isinstance(camfile, ExcellonFile) or (layer_class == 'drill'):
            return DrillLayer.from_cam(camfile)
        elif layer_class == 'internal':
            return InternalLayer.from_cam(camfile)
        if isinstance(camfile, IPCNetlist):
            layer_class = 'ipc_netlist'
        return cls(filename, layer_class, camfile)

    def __init__(self, filename=None, layer_class=None, cam_source=None, **kwargs):
        super(PCBLayer, self).__init__(**kwargs)
        self.filename = filename
        self.layer_class = layer_class
        self.cam_source = cam_source
        self.surface = None
        self.primitives = cam_source.primitives if cam_source is not None else []

    @property
    def bounds(self):
        if self.cam_source is not None:
            return self.cam_source.bounds
        else:
            return None

    def __repr__(self):
        return '<PCBLayer: {}>'.format(self.layer_class)


class DrillLayer(PCBLayer):
    @classmethod
    def from_cam(cls, camfile):
        return cls(camfile.filename, camfile)

    def __init__(self, filename=None, cam_source=None, layers=None, **kwargs):
        super(DrillLayer, self).__init__(filename, 'drill', cam_source, **kwargs)
        self.layers = layers if layers is not None else ['top', 'bottom']


class InternalLayer(PCBLayer):

    @classmethod
    def from_cam(cls, camfile):
        filename = camfile.filename
        try:
            order = int(re.search(r'\d+', filename).group())
        except AttributeError:
            order = 0
        return cls(filename, camfile, order)

    def __init__(self, filename=None, cam_source=None, order=0, **kwargs):
        super(InternalLayer, self).__init__(filename, 'internal', cam_source, **kwargs)
        self.order = order

    def __eq__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order == other.order)

    def __ne__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order != other.order)

    def __gt__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order > other.order)

    def __lt__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order < other.order)

    def __ge__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order >= other.order)

    def __le__(self, other):
        if not hasattr(other, 'order'):
            raise TypeError()
        return (self.order <= other.order)
