import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# constants
NOTION_TOKEN = os.getenv("NOTION_TOKEN")
ALL_MONTH_DB_ID = os.getenv("all_month_db_id")

num_to_month = {
    1: "january",
    2: "february",
    3: "march",
    4: "april",
    5: "may",
    6: "june",
    7: "july",
    8: "august",
    9: "september",
    10: "october",
    11: "november",
    12: "december"
}
headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": "2022-06-28"
}

def get_month():
    while True:
        try:
            month_num = int(input("Enter the month (1-12): ").strip())
            if 1 <= month_num <= 12:
                return num_to_month[month_num]
            print("❌ Month must be between 1 and 12")
        except ValueError:
            print("❌ Please enter a valid number")

def get_notes():
    notes = input("Enter the notes : ").strip()
    if not notes:
        return "will add notes later"
    return notes

def get_notes_to_delete():
    notes = None
    while True:
        notes = input("enter the notes to delete : ").strip().lower()
        if notes:
            break
    
    return notes

def get_category():
    while True:
        category = input("Enter the category : ").strip()
        if category:
            return category
        print("Please enter the Category!")

def get_amount():
    while  True:
        try:
            amt = int(input("Enter amount : ").strip())
            if amt <= 0 : 
                raise ValueError("❌ Amount must be greater than  0")
            return amt
        except ValueError as e:
            print(f"❌ {e}")

def get_date():
    while True:
        user_input = input("Enter the date in yyyy-mm-dd format (leave blank for today): ").strip()
        if not user_input:  
            return datetime.today().strftime("%Y-%m-%d")
        try:
            # validate by parsing
            parsed_date = datetime.strptime(user_input, "%Y-%m-%d")
            return parsed_date.strftime("%Y-%m-%d")  # return as string
        except ValueError:
            print("❌ Please enter a valid date in yyyy-mm-dd format")

def get_daily_db_jsonData(db_id , notes , category , amount , today):
    return {
        "parent" : {"database_id" : db_id} ,
        "properties" : {
            "Notes" : {"title": [{"text": {"content": notes}}]} ,
            "Category" : {"select" : {"name" : category}} ,
            "Amount" : {"number" : amount},
            "Date": {"date": {"start": today}}
        }
    }

def get_pageId_and_currentExp(monthName):
    db_id = os.getenv('all_month_db_id')
    if not db_id:
        print(f"❌ No DB found ")
        return

    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    try :
        res = requests.post(url,headers=headers)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Error in api call : {e}")
        return 
    data = res.json()

    for row in data["results"]:
        month = row["properties"]["Name"]["title"][0]["text"]["content"]
        if month.lower() == monthName.lower():
            pageId = row["id"]
            current_expense = row["properties"]["Total Expense"]["number"] or 0
            return pageId,current_expense
    return None,0

def update_exp(pageId , newAmt):
    url = f"https://api.notion.com/v1/pages/{pageId}"
    data = {
        "properties": {
            "Total Expense": {"number": newAmt}
        }
    }
    res = requests.patch(url, headers=headers, json=data)
    if not res.status_code == 200:
        print("❌ Error:", res.text)    

def increase_monthly_amount(newAmount,monthName):
    # get the current amt
    res = get_pageId_and_currentExp(monthName)
    if res == None: 
        print("Not able to get pageId !")
        return 
    pageId = res[0]
    currentAmt = res[1]
    # now total amount will be
    total_amt = newAmount + currentAmt
    # now edit the data by POST req
    update_exp(pageId,total_amt)
    # confirmation message
    print(f"✅ Updated {monthName}'s total expense from {currentAmt} to {total_amt}")

def reduce_monthly_amount(amountToRemove,monthName):
    # get the current amt
    res = get_pageId_and_currentExp(monthName)
    if res == None: 
        print("Not able to get pageId !")
        return 
    pageId = res[0]
    currentAmt = res[1]
    # now total amount will be
    newTotal = currentAmt - amountToRemove
    # now edit the data by POST req
    update_exp(pageId,newTotal)
    # confirmation message
    print(f"✅ Updated {monthName}'s total expense from {currentAmt} to {newTotal}")

def save_to_notion(db_id,notes,category,amount,today,user_month):
    #api call 
    url = "https://api.notion.com/v1/pages"

    # for daily jo kharcha hua uska data
    daily_json = get_daily_db_jsonData(db_id,notes,category,amount,today)

    try:
        res = requests.post(url , headers=headers , json=daily_json) # new row is being created
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"API Error : {e}")
        return 
    
    print(f"Added Expense to {user_month} month: {category} - {amount} - {today} ✅")

def add_expense():
    # getting the data
    user_month = get_month()
    notes = get_notes()
    category = get_category()
    amount = get_amount()
    today = get_date()

    key = f"{user_month}_{datetime.now().year}_db_id"
    db_id = os.getenv(key)
    if not db_id:
        print(f"❌ No DB found for {user_month}")
        return

    save_to_notion(db_id,notes,category,amount,today,user_month)
    # for updating the total spent in a month
    increase_monthly_amount(amount,user_month)

def detailed_expense(data,category):
    print()
    for row in data["results"]:
        cat = row["properties"]["Category"]["select"]["name"].lower()

        if cat == category:
            note = row["properties"]["Notes"]["title"][0]["text"]["content"]
            amt = row["properties"]["Amount"]["number"]
            date = row["properties"]["Date"]["date"]["start"]
            print(f"{note} - {amt} - {date}")
    print()

def view_expenses():
    user_month = get_month()
    key = f"{user_month}_{datetime.now().year}_db_id"
    db_id = os.getenv(key)
    if not db_id:
        print(f"❌ No DB found for {user_month}")
        return
    
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    try :
        res = requests.post(url,headers=headers)
        res.raise_for_status()
    except Exception as e:
        print(f"❌ Error in api call : {e}")
        return 
    data = res.json()
    
    total = 0
    categories = {}
    for row in data["results"]:
        total += row["properties"]["Amount"]["number"]
        category = row["properties"]["Category"]["select"]["name"].lower()
        if not category in categories:
            categories[category] = 0
        
    for row in data["results"]:
        category = row["properties"]["Category"]["select"]["name"].lower()
        amt = row["properties"]["Amount"]["number"]
        categories[category] += amt
    
    print()
    print(f"Your total expense is {total} Rs. :- ")    
    for cat,amt in categories.items():
        print(f"Expense on {cat} is {amt} i.e. {((amt/total)*100):.2f} %")
    print()

    needDetailed = input("If you want detailed split , press Y/y else N/n : ").strip().lower()
    if needDetailed == "y":    
        while True:
            category = input("Enter the category : ").strip().lower()
            detailed_expense(data,category)

            toContinue = input("To exit , press exit : ").strip().lower()
            if toContinue == "exit":
                break

            else : continue

def delete_expense():
    month = get_month()
    note_to_delete = get_notes_to_delete()
    key = f"{month}_{datetime.now().year}_db_id"
    db_id = os.getenv(key)

    if not db_id:
        print(f"❌ No DB found for {month}")
        return
    
     # Step 1: Find the page with given Notes
    url = f"https://api.notion.com/v1/databases/{db_id}/query"
    payload = {
        "filter": {
            "property": "Notes",
            "title": {
                "equals": note_to_delete
            }
        }
    }
    res = requests.post(url, headers=headers, json=payload)
    data = res.json()
    
    if not data["results"]:
        print(f"❌ No entry found with note: {note_to_delete}")
        return
    
    page_id = data["results"][0]["id"]
    amount = data["results"][0]["properties"]["Amount"]["number"] or 0

    # Step 2: Archive (delete) it
    del_url = f"https://api.notion.com/v1/pages/{page_id}"
    res = requests.patch(del_url, headers=headers, json={"archived": True})

    if res.status_code == 200:
        print(f"✅ Deleted entry with note: {note_to_delete}")
    else:
        print("❌ Error deleting:", res.text)
    
    reduce_monthly_amount(amount,month)
    

def main():
    print("Welcome to notion expense tracker !\n")
    while True:
        print("1. Add a new expense : \n2. View expenses : \n3. Delete an expense : \n4. Exit the app")
        choice = input("Enter your choice : ").strip()

        match choice:
            case "1":
                add_expense()
            case "2":
                view_expenses()
            case "3":
                delete_expense()
            case "4":
                print("😊 Thankyou for ur visit!")
                break
            case _:
                print("Please enter a valid choice !")

if __name__ == "__main__":
    main()