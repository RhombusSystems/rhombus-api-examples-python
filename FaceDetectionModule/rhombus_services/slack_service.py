# Import requests so that we can send POST requests to slack
import requests;

def send_slack_message(url: str, data: dict[str, str]) -> None:
    """Sends a POST request to slack to send a message.

    :param url: The webhook URL
    :param data: The body data of the POST request
    """
    requests.request("POST", url, data=data);
