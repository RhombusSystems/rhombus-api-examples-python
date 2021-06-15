import face_recognition
import pickle;
import cv2
import os;
import glob;

def generate_encodings(names: set[str], force:bool = False):
    if(os.path.exists("res/face_enc") and not force):
        return;
    knownEncodings = []
    knownNames = []
    for name in names:
        files: list[str] = glob.glob("./res/" + name + "/" + "*.jpg");
        print(files);
        for i in range(len(files)):
            file = files[i];

            # load the input image and convert it from BGR (OpenCV ordering)
            # to dlib ordering (RGB)
            image = cv2.imread(file)
            rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

            #Use Face_recognition to locate faces
            boxes = face_recognition.face_locations(rgb,model='hog')

            # compute the facial embedding for the face
            encodings = face_recognition.face_encodings(rgb, boxes)

            # loop over the encodings
            for encoding in encodings:
                knownEncodings.append(encoding)
                knownNames.append(name)

        data = {"encodings": knownEncodings, "names": knownNames}
        f = open("res/face_enc", "wb")
        f.write(pickle.dumps(data))
        f.close()
