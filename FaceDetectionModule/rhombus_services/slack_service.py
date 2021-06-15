import requests;

def send_slack_message(url: str, data: dict[str, str]):
    response = requests.request("POST", url, data=data);
    return response;
