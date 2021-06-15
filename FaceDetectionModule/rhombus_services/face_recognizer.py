import face_recognition
import pickle
import time
import cv2
import os
import glob;

def recognize_faces(path: str) -> set[str]:
    cascPathface = os.path.dirname(cv2.__file__) + "/data/haarcascade_frontalface_alt2.xml"
    faceCascade = cv2.CascadeClassifier(cascPathface)
    data = pickle.loads(open('res/face_enc', "rb").read())
    image = cv2.imread(path);
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = faceCascade.detectMultiScale(gray,
                                     scaleFactor=1.1,
                                     minNeighbors=5,
                                     minSize=(60, 60),
                                     flags=cv2.CASCADE_SCALE_IMAGE)

    encodings = face_recognition.face_encodings(rgb);
    names: set[str] = set()
    for encoding in encodings:
        #Compare encodings with encodings in data["encodings"]
        #Matches contain array with boolean values and True for the embeddings it matches closely
        #and False for rest
        matches = face_recognition.compare_faces(data["encodings"],
        encoding)
        #set name =inknown if no encoding matches
        name = "Unknown"
        # check to see if we have found a match
        if True in matches:
            #Find positions at which we get True and store them
            matchedIdxs = [i for (i, b) in enumerate(matches) if b]
            counts = {}
            # loop over the matched indexes and maintain a count for
            # each recognized face face
            for i in matchedIdxs:
                #Check the names at respective indexes we stored in matchedIdxs
                name = data["names"][i]
                #increase count for the name we got
                counts[name] = counts.get(name, 0) + 1
                #set name which has highest count
                name = max(counts, key=counts.get)
    
    
            # update the list of names
            names.add(name)
            #  for ((x, y, w, h), name) in zip(faces, names):

    return names;

def recognize_faces_in_directory(directory: str) -> set[str]: 
    files: list[str] = glob.glob(directory + "*.jpg");
    names: set[str] = set();
    for i in range(len(files)):
        file: str = files[i];
        res = recognize_faces(path=file);
        names.update(res);

    return names;

        
