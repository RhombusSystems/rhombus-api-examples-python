# Import type hints
from typing import List
from typing import Tuple

# Import Numpy and OpenCV for neural network processing
import numpy as np
import cv2

# Import glob to get all of the frames in the clip directory
import glob

# Import FootageBoundingBoxType to create our list of bounding boxes
from RhombusAPI.models.footage_bounding_box_type import FootageBoundingBoxType
from RhombusAPI.models.activity_enum import ActivityEnum

# Import vector to define positions and dimensions easily
from helper_types.vector import Vec2


class BoundingBox:
    """Data for bounding boxes

    :attribute label: Label for this box, for example "cat", "table", "human", etc...
    :attribute position: Position of the bounding box
    :attribute dimensions: Dimensions of the bounding box
    :attribute timestamp: The timestamp in ms of where to put the bounding box
    """

    label: str
    position: Vec2
    dimensions: Vec2
    timestamp: int

    def __init__(self, label: str, position: Vec2, dimensions: Vec2, timestamp: int) -> None:
        """Constructor for bounding boxes which initializes all of the attributes

        :param label: Label for this box, for example "cat", "table", "human", etc...
        :param position: Position of the bounding box
        :param dimensions: Dimensions of the bounding box
        :param timestamp: The timestamp in ms of where to put the bounding box
        """
        self.label = label
        self.position = position
        self.dimensions = dimensions
        self.timestamp = timestamp


def classify_image(yolo_net: cv2.dnn_Net, coco_classes: List[str], layer_names: List[str], file_path: str,
                   timestamp: int, confidence_threshold: float = 0.7) -> Tuple[List[BoundingBox], Vec2]:
    """Classify a specific JPEG image from a given file_path

    :param yolo_net: The YOLO neural network that is loaded at startup
    :param coco_classes: The COCO class names that is loaded at startup
    :param layer_names: The list of layer names in the neural net
    :param file_path: The path of the JPEG image to classify
    :param timestamp: The timestamp in ms at which this JPEG appears
    :param confidence_threshold: The minimum threshold at which a bounding box will be added, default is 0.7
    :return: Returns the list of bounding boxes found in the JPEG and the dimensions (width and height) of the JPEG
    """

    # Load the image from the file path through OpenCV
    img = cv2.imread(file_path)

    # Load the blob from our image
    blob = cv2.dnn.blobFromImage(img, 1 / 255.0, (416, 416), swapRB=True, crop=False)

    # Set this blob as our input into COCO
    yolo_net.setInput(blob)

    # Set the output layer using our layer_names
    outputs = yolo_net.forward(layer_names)

    # Get the dimensions of our image
    dimensions = Vec2(0, 0)
    dimensions.x, dimensions.y = img.shape[:2]

    # These are the output lists which we will use to construct our bounding boxes
    _boxes: List[list[int]] = []
    _confidences: List[float] = []
    _classIDs = []

    # Loop through all of our outputs
    for output in outputs:
        for detection in output:
            # Get our scores, classID, and confidence
            scores = detection[5:]
            classID = np.argmax(scores)
            confidence = scores[classID]

            # We are only going to add the boxes that pass our confidence_threshold
            if confidence > confidence_threshold:
                # Get our box
                box = detection[:4] * np.array([dimensions.x, dimensions.y, dimensions.x, dimensions.y])
                (center_x, center_y, width, height) = box.astype("int")
                x = int(center_x - (width / 2))
                y = int(center_y - (height / 2))

                # Construct a list of ints to represent our box
                box = [x, y, int(width), int(height)]

                # Append all of our data to our lists
                _boxes.append(box)
                _confidences.append(float(confidence))
                _classIDs.append(classID)

    # Gets the indices of our boxes using non maximum suppression. We are just using 0.4 as the threshold for this example, however this is can obviously be configured
    indices = cv2.dnn.NMSBoxes(_boxes, _confidences, confidence_threshold, 0.4)

    # Create our final output BoundingBox
    boxes: List[BoundingBox] = []

    # Only process our indices if there actually are any elements
    if (len(indices) == 0):
        return boxes, dimensions

    # Loop through our indices
    for i in indices.flatten():
        # X and Y position of our box
        (x, y) = (_boxes[i][0], _boxes[i][1])

        # Width and height of our box
        (w, h) = (_boxes[i][2], _boxes[i][3])

        # Create and append our new box
        box = BoundingBox(label=coco_classes[_classIDs[i]], position=Vec2(x, y), dimensions=Vec2(w, h),
                          timestamp=timestamp)
        boxes.append(box)

    # Return our data
    return boxes, dimensions


def classify_directory(yolo_net: cv2.dnn_Net, coco_classes: List[str], directory: str, start_time: int,
                       duration: int) -> List[FootageBoundingBoxType]:
    """Classify all frames in the directory. 

    :param yolo_net: The YOLO neural network that is loaded at startup
    :param coco_classes: The COCO class names that is loaded at startup
    :param directory: The directory containing the clip.mp4 and frame JPEGs to process. This is normally "res/<TIMESTAMP_SECONDS>/" 
    :param start_time: The start time in seconds of our clip.mp4
    :param duration: The duration in seconds of our clip
    :return: Returns the list of FootageBoundingBoxType which we can then just send to Rhombus to create the bounding boxes on the console
    """

    # Get the names of the layers in our net
    layer_names: List[str] = yolo_net.getLayerNames()
    layer_names = [layer_names[i[0] - 1] for i in yolo_net.getUnconnectedOutLayers()]

    # Get all of the JPEGs in our directory
    files: List[str] = glob.glob(directory + "*.jpg")

    # Sort these files so that we make sure we are processing frames in order
    files = sorted(files, key=str.lower)

    # Create a sort of megalist of Bounding boxes which will hold all of the BoundingBoxes of all of the frames
    boxes: List[BoundingBox] = []

    # The final dimensions of our image
    dimensions: Vec2 = Vec2(0, 0)

    # Loop through all of our files
    for i in range(len(files)):
        # The file path
        file = files[i]

        # Get the timestamp of our frame, which will be the start_time in seconds + some offset
        # The offset will just be the index / the number of files * our duration, that way we can see what fraction of the way we are through our clip just by looking at the index
        # We also will multiply everything by 1000 since the timestamp has to be in ms, and right now we are in seconds
        timestamp = (start_time + (i / len(files)) * duration) * 1000

        # Classify our JPEG
        res, dim = classify_image(yolo_net, coco_classes, layer_names, file, int(timestamp))

        # Add those results to our megalist
        boxes = boxes + res

        # Update the dimensions of our JPEG just in case
        dimensions = dim

    # Create our final list of boxes
    boundingBoxes: List[FootageBoundingBoxType] = []

    # Loop through all of our own boxes and convert them to FootageBoundingBoxTypes
    for i in range(len(boxes)):
        box = boxes[i]

        # We are using the top left as the bounding box position, so top left is (box.x, box.y), bottom right is (box.x + box.width, box.y + box.height)
        boundingBoxes.append(FootageBoundingBoxType(
            a=ActivityEnum.CUSTOM,
            # These values are permyriads, so we need to convert our bounding boxes appropriately
            b=(box.position.y + box.dimensions.y) / dimensions.y * 10000,  # Bottom
            l=(box.position.x / dimensions.x) * 10000,  # Left
            r=((box.position.x + box.dimensions.x) / dimensions.x) * 10000,  # Right
            t=(box.position.y / dimensions.y) * 10000,  # Top
            ts=box.timestamp,
            cdn=box.label
        ))

    for i in range(len(boundingBoxes)):
        print("Found object " + str(boundingBoxes[i].cdn))

    # Return those boxes
    return boundingBoxes
