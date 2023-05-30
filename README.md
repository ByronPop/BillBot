# BillBot
A Twitter bot to help you stay informed with the state legislature. Concise ChatGPT powered summaries and analysis of every bill introduced in every U.S. state.

## Background

Hi everyone, my name is Byron and if you know me you know that I love chatGPT. Like many, I have a casual interest in politics, particularly local politics, as it tends to more directly impact my life. However, staying informed about newly introduced legislation can be challenging. Local news coverage is sparse, and who has time to decipher lengthy legislative bills?

That's where BillBot comes in! BillBot is a Twitter bot I created that helps you stay informed with local legislation.  Each week, BillBot finds the latest bills that have been introduced in your state, passes the bill text to chatGPT, and then posts an analysis of the legislation on Twitter in the form of a succinct thread. The analysis includes:
- A brief summary of the bill
- An advocate opinion
- An opposition opinion
- The affected population

In a few short tweets you can stay up to date on all that’s happening in you.

https://twitter.com/WABillBot

<img src="https://github.com/ByronPop/BillBot/assets/33380363/7b50d559-6a95-49e8-b10f-b61b7e0c194e" width="450"/> <img src="https://github.com/ByronPop/BillBot/assets/33380363/5a75f609-4a7c-4d4a-9bec-e439f21eb2d8" width="450"/> 

## How it Works
I wrote the script for BillBot in Python and leveraged 3 public APIs and some webscraping to pull the legislative bill data, pass it to ChatGPT and then post the analysis to Twitter. 

### Legislative Data
Openstates.org (https://openstates.org/) offers a free public API that contains legislative data for every U.S state. To get the Bill data, I call the /bills endpoint and retrieve all of the bills introduced in a state during the last week

```
def fetch_congressional_bills(input_state):
    # set up API key and base URL
    headers = {'x-api-key': 'bd9aacfd-c090-4292-9a75-561638b815fe', 'accept': 'application/json'}
    url = 'https://v3.openstates.org/bills'

    # Calculate the date range for the last week
    start_date = (datetime.datetime.now() - timedelta(days=7)).date().strftime('%Y-%m-%d')

    # set up parameters for bills introduced in the last week in WA
    params = {'jurisdiction': input_state, 'created_since': f'{start_date}', 'classification': 'bill', 'sort': 'updated_desc'}

    # make API request
    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        data = json.loads(response.text)
        print(f"Total bills fetched: {len(data)}")
        return data
    else:
        print(f"Error fetching bills: {response.status_code}")
        return None

```


### ChatGPT Integration



### Twitter Integration


