# Import OpenCV and FaceRecognition to do facial recognition on images
import face_recognition;
import cv2;

# Import pickle to load our encodings
import pickle;

# Import OS and Glob to get all of our files
import os;
import glob;

def recognize_faces(path: str) -> set[str]:
    """Recognize all of the faces found in a specific image

    :param path: The path of the image to analyze
    :return: The set of faces found in the image
    """

    # Load the haarcascade OpenCV File
    casc_pathface = os.path.dirname(cv2.__file__) + "/data/haarcascade_frontalface_alt2.xml";

    # Create the face cascade
    face_cascade = cv2.CascadeClassifier(casc_pathface);

    # Load our encodings created in encoding_generator.py
    data = pickle.loads(open('res/face_enc', "rb").read());

    # Read the image from our source path
    image = cv2.imread(path);

    # Convert our image from BGR to RGB
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB);

    # Grayscale our image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY);

    # Detect all of the faces in our image
    faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60), flags=cv2.CASCADE_SCALE_IMAGE);

    # Get the encodings from our rgb image
    encodings = face_recognition.face_encodings(rgb);

    # Names will hold all of the names identified
    names: set[str] = set();

    # Loop over all of our encodings
    for encoding in encodings:

        # Get our matches by comparing faces
        matches = face_recognition.compare_faces(data["encodings"], encoding);

        # Name will be the name of the found person
        name = "Unknown"

        # If we have a match
        if True in matches:

            # Find all of the matched Ids
            matched_ids = [i for (i, b) in enumerate(matches) if b];
            counts = {};

            # Loop through our matched_ids
            for i in matched_ids:

                # Get the name from our ID
                name = data["names"][i];

                # Increment the counter for our name
                counts[name] = counts.get(name, 0) + 1;

                # Name will be the name for which we have the highest count of
                name = max(counts, key=counts.get);
    
    
            # Add the name to our list of names
            names.add(name)

    # Return our data
    return names;

def recognize_faces_in_directory(directory: str) -> set[str]: 
    """Find faces for all of the images in a directory

    :param directory: The directory to find faces in
    :return: The set of faces found in the directory of images
    """

    # Get all of the files in the specified directory
    files: list[str] = glob.glob(directory + "*.jpg");

    # Names will hold all of the names identified
    names: set[str] = set();

    # Loop through all of our files
    for i in range(len(files)):

        # Hold our file
        file: str = files[i];

        # Recognize all of the faces in our file
        res = recognize_faces(path=file);

        # Add the found faces to our set
        names.update(res);

    # Return our data
    return names;

        
