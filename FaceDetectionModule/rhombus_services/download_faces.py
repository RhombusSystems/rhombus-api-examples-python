# Import OS and IO to open files and write data
import os;
import io;

# Import requests to download the images
import requests;

# Import RhombusAPI to send requests to rhombus to get the recent face events
import RhombusAPI as rapi;
    
def get_rhombus_image (key: str) -> str: 
    """Return the full uri of a face image given an aws s3 key

    :param key: The key to get the URI for
    :return: The full URI of the image
    """
    return "https://media.rhombussystems.com/media/faces?s3ObjectKey=" + key;

def save_image(headers: dict[str, str], file: io.BufferedWriter, http_client: requests.sessions.Session, key: str) -> None:
    """Save an image aws s3 key to a file

    :param headers: The headers to use when sending the request to the URI. These are typically authentication headers
    :param file: The output writer to write our data to
    :param http_client: The HTTP Client intialized at startup to send requests to our URI
    :param key: The aws s3 key
    """

    # Get our full URI
    uri = get_rhombus_image(key);
    print("Saving face image from " + uri);

    # Download the file from the uri
    buffer = http_client.get(uri, headers=headers)

    # Write the file
    file.write(buffer.content)

    # Flush our file and buffer
    file.flush()
    buffer.close()

def download_faces(api_key: str, api_client: rapi.ApiClient, http_client: requests.sessions.Session) -> set[str]:
    """Download all recent face events to res

    :param api_key: The Rhombus API key specified by the user to use to send requests
    :param api_client: The Rhombus API client intialized at startup to send Rhombus API requests with
    :param http_client: The HTTP Client intialized at startup to send requests to our URI
    :return: The list of faces that can be matched with
    """

    # Get all faces saved by Rhombus
    api = rapi.FaceWebserviceApi(api_client=api_client);
    res = api.get_faces_v2();

    # The set of face names which we will use
    faces: set[str] = set([]);

    # Loop through all of the faces Rhombus gives us
    for face in res.faces:
        # And add them to the set
        faces.add(face.name)

    # Create our headers which will be used to download our images
    headers = {
            # These headers below are necessary for almost all Rhombus requests, URL or API regardless
            "x-auth-apikey": api_key,
            "x-auth-scheme": "api-token",
            "Accept": "application/json",
            "Content-Type": "application/json" 
    }

    # Loop through all of our faces
    for face in faces:
        # The output directory is usually res/<FACE_NAME>
        dir: str = "./res/" + face;

        # If the directory doesn't exist, then we need to create it
        if(not os.path.exists(dir)):
            os.mkdir(dir);
            
        # Get all of the recent face events for our name
        res = api.get_recent_face_events_for_name(body=rapi.FaceGetRecentFaceEventsForNameWSRequest(face_name=face));

        # Loop through all of our events
        for event in res.face_events:
            # Get the thumbnail key
            key: str = event.thumbnail_s3_key;

            # If the key exists (sometimes it may not)
            if(key is not None):
                # The output path will be res/<FACE_NAME>/<event UUID>.jpg
                path: str = "./res/" + face + "/" + event.uuid + ".jpg";
                if(not os.path.exists(path)):
                    with open(path, "wb") as file:
                        save_image(headers=headers, file=file, http_client=http_client, key=key);
                    file.close();
    return faces;
