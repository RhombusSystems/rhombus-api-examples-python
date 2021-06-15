import requests;
import os;
import io;

import RhombusAPI as rapi;
    
def get_rhombus_image (key: str): 
    return "https://media.rhombussystems.com/media/faces?s3ObjectKey=" + key;

def save_image(headers: dict[str, str], file: io.BufferedWriter, http_client: requests.sessions.Session, key: str):
    uri = get_rhombus_image(key);
    print("Saving image " + uri);
    # Download the file from the uri
    buffer = http_client.get(uri, headers=headers)

    # Write the file
    file.write(buffer.content)

    # Flush our file and buffer
    file.flush()
    buffer.close()

class Face:
    name: str;
    face_id: str;
    org_uuid: str;

    def __init__(self, name: str, face_id: str, org_uuid: str):
        self.name = name;
        self.face_id = face_id;
        self.org_uuid = org_uuid;

def download_faces(api_key: str, api_client: rapi.ApiClient, http_client: requests.sessions.Session) -> set[str]:
    api = rapi.FaceWebserviceApi(api_client=api_client);
    res = api.get_faces_v2();

    faces: set[str] = set([]);
    for face in res.faces:
        faces.add(face.name)

    headers = {
            # These headers below are necessary for almost all Rhombus requests, URL or API regardless
            "x-auth-apikey": api_key,
            "x-auth-scheme": "api-token",
            "Accept": "application/json",
            "Content-Type": "application/json" 
    }

    for face in faces:
        dir: str = "./res/" + face;
        if(not os.path.exists(dir)):
            os.mkdir(dir);
            
        res = api.get_recent_face_events_for_name(body=rapi.FaceGetRecentFaceEventsForNameWSRequest(face_name=face));


        for event in res.face_events:
            key: str = event.thumbnail_s3_key;
            if(key is not None):
                path: str = "./res/" + face + "/" + event.uuid + ".jpg";
                if(not os.path.exists(path)):
                    with open(path, "wb") as file:
                        save_image(headers=headers, file=file, http_client=http_client, key=key);
                    file.close();
    return faces;
