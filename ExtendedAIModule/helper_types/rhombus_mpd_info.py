###################################################################################
# Copyright (c) 2021 Rhombus Systems                                              #
#                                                                                 #
# Permission is hereby granted, free of charge, to any person obtaining a copy    #
# of this software and associated documentation files (the "Software"), to deal   #
# in the Software without restriction, including without limitation the rights    #
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell       #
# copies of the Software, and to permit persons to whom the Software is           #
# furnished to do so, subject to the following conditions:                        #
#                                                                                 #
# The above copyright notice and this permission notice shall be included in all  #
# copies or substantial portions of the Software.                                 #
#                                                                                 #
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR      #
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,        #
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE     #
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER          #
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,   #
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE   #
# SOFTWARE.                                                                       #
###################################################################################

import re
import xml.etree.ElementTree as ET


class RhombusMPDInfo:
    def __init__(self, raw_doc):
        raw_doc = re.sub(' xmlns="[^"]+"', '', raw_doc, count=1)
        tree = ET.ElementTree(ET.fromstring(raw_doc))

        root = tree.getroot()

        segment_template = root.find("./Period/AdaptationSet/SegmentTemplate")
        self.segment_pattern = segment_template.attrib['media']
        self.init_string = segment_template.attrib['initialization']
        self.start_index = int(segment_template.attrib['startNumber'])
