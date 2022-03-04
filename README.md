# Welcome to Rhombus Systems

Rhombus Systems was built on a foundation of API-driven micro-services. As a result, a deep and comprehensive set of API
endpoints exist and are made available to our customers. These API contracts are not an afterthought, but are actually
used by internal Rhombus software. This means that anything that the system is capable of doing can also be done via the
Rhombus API.

This Repository is home to Python based examples for many of the endpoints of Rhombus Systems' API, examples for other
common languages can be found [here.](https://github.com/RhombusSystems)

To get started and explore the API's
Documentation, [Click Here!](https://apidocs.rhombussystems.com/reference/introduction)

For answers to Frequently Asked
Questions, [Click Here!](https://support.rhombussystems.com/hc/en-us/sections/115002570508-FAQ)

# Examples in this Repository

**example_Name.py**

What does this example do?

**API Endpoints**

- Which endpoints does this example use?

**Dependencies**

- Does this example have any external dependencies?

## add_or_remove_labels.py

This example batch modifies labels based on CLAs

#### API Endpoints

- [face/addFaceLabel](https://apidocs.rhombussystems.com/reference/addfacelabel)
- [face/removeFaceLabel](https://apidocs.rhombussystems.com/reference/removefacelabel)

## climate_create_seekpoint.py

This example gets the rate of change of the temperature.

#### API Endpoints

- [climate/getMinimalClimateStateList](https://apidocs.rhombussystems.com/reference/getminimalclimatestatelist)
- [climate/getClimateEventsForSensor](https://apidocs.rhombussystems.com/reference/getclimateeventsforsensor)
- [camera/getMinimalCameraStateList](https://apidocs.rhombussystems.com/reference/getminimalcamerastatelist)
- [camera/createFootageSeekpoints](https://apidocs.rhombussystems.com/reference/createfootageseekpoints)

## copy_footage_to_local_storage.py

This example pulls footage from a camera on LAN and stores it to the filesystem.

#### API Endpoints

- [org/generateFederatedSessionToken](https://apidocs.rhombussystems.com/reference/generatefederatedsessiontoken)
- [camera/getMediaUris](https://apidocs.rhombussystems.com/reference/getmediauris-1)

## door_report.py

This example gets a report of the recent door openings and closings.

#### API Endpoints

- [location/getLocations](https://apidocs.rhombussystems.com/reference/getlocations)
- [door/getMinimalDoorStateList](https://apidocs.rhombussystems.com/reference/getminimaldoorstatelist)
- [door/getDoorEventsForSensor](https://apidocs.rhombussystems.com/reference/getdooreventsforsensor)

## face_report.py

This example gets a report of the recent faces and downloads the pictures of each face.

#### API Endpoints

- [proximity/getMinimalProximityStateList](https://apidocs.rhombussystems.com/reference/getminimalproximitystatelist)
- [face/getRecentFaceEventsV2](https://apidocs.rhombussystems.com/reference/getrecentfaceeventsv2)

## get_frame.py

This example pulls a frame from a camera on LAN and saves it.

#### API Endpoints

- [video/getExactFrameUri](https://apidocs.rhombussystems.com/reference/getexactframeuri)

## licenseplate_report.py

This example gets a report of recent licenseplates and downloads the pictures of each one.

#### API Endpoints

- [camera/getMinimalCameraStateList](https://apidocs.rhombussystems.com/reference/getminimalcamerastatelist)
- [vehicle/getRecentVehicleEvents](https://apidocs.rhombussystems.com/reference/getrecentvehicleevents)

## LiveStreamingExample

This example demonstrates how to re-stream Rhombus live camera footage to a web client.

#### API Endpoints

- [camera/getMediaUris](https://apidocs.rhombussystems.com/reference/getcameramediauris)
- [org/generateFederatedSessionToken](https://apidocs.rhombussystems.com/reference/generatefederatedsessiontoken)

## tag_filter_stats.py

This example filters through tag movements and creates CSV file..

#### API Endpoints

- [proximity/getMinimalProximityStateList](https://apidocs.rhombussystems.com/reference/getminimalproximitystatelist)
- [location/getLocations](https://apidocs.rhombussystems.com/reference/getlocations)
- [proximity/getLocomotionEventsForTag](https://apidocs.rhombussystems.com/reference/getlocomotioneventsfortag)

## timelapse_saver.py

This example creates a timelapse and saves it in a file.

#### API Endpoints

- [camera/getMinimalCameraStateList](https://apidocs.rhombussystems.com/reference/getminimalcamerastatelist)
- [video/getTimelapseClips](https://apidocs.rhombussystems.com/reference/gettimelapseclips)
- [video/generateTimelapseClip](https://apidocs.rhombussystems.com/reference/generatetimelapseclip)

## user_list.py

This example gets a report of all of the Users and their emails.

#### API Endpoints

- [user/getUsersInOrg](https://apidocs.rhombussystems.com/reference/getusersinorg)

## video_clip_report.py

This example creates and downloads a clip and accompanying report.

#### API Endpoints

- [camera/getMinimalCameraStateList](https://apidocs.rhombussystems.com/reference/getminimalcamerastatelist)
- [video/spliceV2](https://apidocs.rhombussystems.com/reference/splicev2)
- [event/getClipsWithProgress](https://apidocs.rhombussystems.com/reference/getclipswithprogress)
- [event/getSavedClipDetails](https://apidocs.rhombussystems.com/reference/getsavedclipdetails)

## webhook.py

This example creates a webhook in the Rhombus console and downloads video footage of notified alerts through the
webhook.

#### API Endpoints

- [org/generateFederatedSessionToken](https://apidocs.rhombussystems.com/reference/generatefederatedsessiontoken)
- [integrations/updateWebhookIntegration](https://apidocs.rhombussystems.com/reference/updatewebhookintegration)