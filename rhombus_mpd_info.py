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
