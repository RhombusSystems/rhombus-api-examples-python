import face_recognition
import pickle;
import cv2
import os;
import glob;

def generate_encodings(names: set[str], force: bool = False) -> None:
    """Generates face encodings for OpenCV using faces downloaded in res

    :param names: The list of names to match for so that we can find their corresponding directories. These will follow the pattern res/<NAME>
    :param force: If this is false, then if res/face_enc exists this function will not recreate the encodings. If it is true, it will create the encodings recardless
    """
    # If the user has not asked to force the creation of encodings and the res/face_enc file exists, then we don't need to run this function
    if(os.path.exists("res/face_enc") and not force):
        return;

    # These lists will hold our names and encodings which will be written to the file
    known_encodings = []
    known_names = []

    # Loop through all of the names
    for name in names:

        # Get all of the JPEG face images of the specific name
        files: list[str] = glob.glob("./res/" + name + "/" + "*.jpg");

        # Loop through all of the files
        for i in range(len(files)):

            # Hold our file
            file = files[i];

            # Load the file
            image = cv2.imread(file)

            # Convert the image from BGR to RGB
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            # Get all of the recognized faces and their boxes
            boxes = face_recognition.face_locations(rgb,model='hog')

            # Get all of the encodings of the faces
            encodings = face_recognition.face_encodings(rgb, boxes)

            # Loop through all of the encodings and add them to our list
            for encoding in encodings:
                known_encodings.append(encoding)
                known_names.append(name)

        # Combine our data
        data = {"encodings": known_encodings, "names": known_names}

        # Open our output file
        f = open("res/face_enc", "wb")

        # Dump our data
        f.write(pickle.dumps(data))

        # Close the output file
        f.close()
