from bs4 import BeautifulSoup
from PIL import Image
import requests
from requests_html import HTMLSession
from urllib.parse import urljoin
from selenium import webdriver
import os

# References used:
# https://stackoverflow.com/questions/54338681/how-to-download-images-from-websites-using-beautiful-soup
# https://beautiful-soup-4.readthedocs.io/en/latest/index.html?highlight=tag#
# https://www.thepythoncode.com/article/extracting-and-submitting-web-page-forms-in-python


def get_card_info(main_site, card_id):
    """
    Given a card ID, print its information (effects, power, etc.)
    :param main_site: string, holds main site to go to
    :param card_id: string, card ID
    :return stats_dict: contains dictionary of formatted information about the card
    """
    # access site to pull data from
    url = main_site + "/cardlist/list/?cardno=" + card_id
    contents = requests.get(url)
    soup = BeautifulSoup(contents.text, 'html.parser')
    stats_dict = {}

    # filter out card image information
    def graphic_filter(css_class):
        return css_class != "graphic"

    # get "th" and "td" tags for the status information table
    stats_headers = soup.find(class_="status").find_all("th", class_=graphic_filter)
    stats_content = soup.find(class_="status").find_all("td", class_=graphic_filter)

    # get card name from the span tag
    stats_dict["Card Name"] = soup.find(class_="status").find("span", class_="kana").text

    # search for card image
    card_img = soup.find("td", class_="graphic").img

    # get card image link and isolate card ID
    stats_dict["Card Img"] = url + card_img["src"]

    # exclude card name row from headers and content
    for h, d in zip(stats_headers[1:], stats_content[1:]):
        #print((h.text, d.text))
        if h.text == "Color":
            # isolate color name from file location
            stats_dict[h.text] = d.next_element["src"].split("/")[-1].split(".")[0].capitalize()

        elif h.text == "Side":
            # fill in either Weiss for "w" or Schwarz for "s"
            if d.next_element.next_element["src"].split("/")[-1].split(".")[0] == "w":
                stats_dict[h.text] = "Weiss"
            else:
                stats_dict[h.text] = "Schwarz"

        elif h.text == "Soul":
            # handles cards with soul
            if d.text == "":
                stats_dict[h.text] = str(len(d))
            else:
                stats_dict[h.text] = "-"

        elif h.text == "Trigger":
            if d.text == "":
                # isolate trigger from file location
                if d.next_element != "\n":
                    stats_dict[h.text] = d.next_element["src"].split("/")[-1].split(".")[0].capitalize()
                else:
                    stats_dict[h.text] = "-"
        else:
            # strip newlines and carriage returns
            stats_dict[h.text] = d.text.replace("\n", "").replace("\r","")

    return stats_dict


def card_search():
    """
    Queries the Weiss Schwarz website and extracts its search forms to be filled by user input.
    :return: List of cards and its information stored in a dictionary form returned by get_card_info().
    """
    main_site = "https://en.ws-tcg.com"
    url = main_site + "/cardlist/cardsearch/exec"
    session = HTMLSession()
    res = session.get(url)
    soup = BeautifulSoup(res.content, "lxml")

    # find the card search forms
    initial_form = soup.find("form", class_="cardSearchForm")
    forms = soup.find("form", class_="cardSearchForm").table.find_all("td")

    # create a dictionary of the required forms to fill out
    details = {}
    action = initial_form.attrs.get("action").lower()
    method = initial_form.attrs.get("method", "get").lower()
    inputs = []
    target_input_methods = ["text", "checkbox", "hidden", "submit"]
    for input_tag in forms:
        query_input = input_tag.find_all("input")
        if query_input:
            for item in query_input:
                if item["type"] in target_input_methods:
                    in_type = item["type"]
                    in_name = item["name"]
                    in_value = item.attrs.get("value","")
                    in_id = ""
                    if "id" in item.attrs.keys():
                        in_id = item["id"]

                    inputs.append({"type": in_type, "id": in_id, "name": in_name, "value": in_value})

        query_select = input_tag.find_all("select")
        if query_select:
            for item in query_select:
                in_type = "select"
                in_name = item["name"]
                in_value = item.attrs.get("value","")
                options = []
                select_tags = item.contents
                for elem in select_tags:
                    options.append((elem["value"], elem.text))
                inputs.append({"type": in_type, "name": in_name, "value": in_value, "options": options})

    details["action"] = action
    details["method"] = method
    details["inputs"] = inputs

    # create data to be submitted
    data = {}
    for input_tag in details["inputs"]:
        if input_tag["type"] == "hidden":
            data[input_tag["name"]] = input_tag["value"]
        elif input_tag["type"] != "submit":
            if input_tag["type"] == "select":
                name = input_tag["name"]
                # flag for staying inside selection tag
                option_keys = [item_tuple[0] for item_tuple in input_tag["options"]]
                in_selection = True
                while in_selection:
                    value = input("Enter value for '%s' (input type: %s) (type 'o' to see options): " % (name, input_tag["type"]))
                    if value.lower() == "o":
                        # flag for staying inside selection tag's option pages
                        in_pages = True
                        page = 1
                        while in_pages:
                            # pages are separated by showing 10 items at a time
                            start_index = 10
                            end_index = 10
                            print("=" * 15 + " %s Options: " % input_tag["name"] + "=" * 15)
                            page_items = input_tag["options"][start_index * (page - 1):end_index * page]
                            for item in page_items:
                                print("%s  Key: %s" % (item[1], item[0]))
                            print("=" * 15 + "=" * 15, "\n(Current page: %d)" % page)
                            prompt = input("Enter key or  type 'prev'/'next' to navigate pages: ")
                            if prompt.lower() in ("prev", "p"):
                                if page > 1:
                                    page -= 1
                                start_index *= (page - 1)
                                end_index *= page
                                print(input_tag["options"][start_index * page:int(end_index * page)], "=" * 15 + "=" * 15,
                                      "\n(Current page: %d)" % page)
                            elif prompt.lower() in ("next", "n"):
                                if (end_index * page) > len(input_tag["options"]):
                                    # properly display the last page if not a multiple of 10
                                    end_index = -1
                                    start_index *= page
                                else:
                                    page += 1
                                    end_index *= page
                                    start_index *= (page - 1)

                                print(input_tag["options"][start_index * page:int(end_index * page)], "=" * 15 + "=" * 15,
                                      "\n(Current page: %d)" % page)
                            else:
                                if prompt.lower() in option_keys:
                                    data[input_tag["name"]] = prompt.lower()
                                    in_pages = False
                                    in_selection = False
                                else:
                                    print("%s not found in keys. Please try again." % prompt)

                    elif value.lower() in option_keys:
                        data[input_tag["name"]] = value.lower()
                        in_selection = False
                    else:
                        print("%s not found in keys. Please try again." % value)

            else:
                name = input_tag["id"]
                value = input("Enter value for '%s' (input type: %s): " % (name, input_tag["type"]))
                if value == "":
                    if input_tag["type"] == "checkbox":
                        data[input_tag["name"]] = 1
                    else:
                        data[input_tag["name"]] = input_tag["value"]
                else:
                    data[input_tag["name"]] = value


    # submit forms to site
    new_url = urljoin(url, details["action"])
    if details["method"] == "post":
        res = session.post(new_url, data=data)
    elif details["method"] == "get":
        res = session.get(new_url, params=data)

    s = BeautifulSoup(res.content, "lxml")

    card_results = []
    print("Compiling results...")

    # gather all of the cards on page 1
    search = s.find("div", id="searchResults").find("table", id="searchResult-table")
    card_links = search.find_all("th")
    for card in card_links:
        card_info = get_card_info(main_site, card.a["href"].split("=")[1])
        card_results.append(card_info)

    # check if search results have multiple pages
    pages = s.find("p", class_="pageLink")
    # check for an ellipsis span which indicate multiple pages
    # TODO: fix multiple pages
    span_check = pages.find_all("span")
    if span_check:
        page_links = pages.find_all("a")[:-2]
    else:
        page_links = pages.find_all("a")[:-1]
    if page_links:
        for page in page_links:
            new_link = main_site + page["href"]

            new_url = urljoin(new_link, details["action"])
            next_page = ""
            if details["method"] == "post":
                next_page = session.post(new_url, data=data)
            elif details["method"] == "get":
                next_page = session.get(new_url, params=data)

            h = BeautifulSoup(next_page.content, "lxml")
            cards = h.find("div", id="searchResults").find("table", id="searchResult-table").find_all("th")
            # for card in cards:
            #     card_info = get_card_info(main_site, card.a["href"].split("=")[1])
            #     card_results.append(card_info)

    print("Finished compilation.")
    return card_results


def save_cards(card_list):
    """
    Opens a card list and saves information as a .txt file saved as 'card_info.txt'.
    :param card_list: Card list to be saved. Each card is a dictionary with card information stored inside.
    """
    with open("card_info.txt", "w+", encoding="utf8") as card_file:
        for card in card_list:
            keys = list(card.keys())
            values = list(card.values())
            card_file.write("="*20 + "\n")
            for i in range(len(card.keys())):
                card_file.write("%s: %s\n" % (keys[i], values[i]))
            card_file.write("="*20 + "\n")


def main():
    # get site and URL of a card's stats
    # main site URL used later for getting image link
    main_site_url = "https://en.ws-tcg.com"
    url = "https://en.ws-tcg.com/cardlist/list/?cardno=FZ/S17-TE04"
    # extract page and convert to HTML
    #r = requests.get(url)
    #soup = BeautifulSoup(r.text, 'html.parser')

    # search for card image
    #card_img = soup.find("td", class_="graphic").img
    #print(card_img)
    # get card image link and isolate card ID
    #card_img_link = main_site_url + card_img["src"]
    #print(card_img_link)
    #card_id = card_img["src"].split("/")[-1].split(".")[0]

    #test_id = "FZ/S17-TE04"
    # original LSS/W45-E005
    # test AB/W31-E058
    # climax 1 AB/W31-E101

    test_id = "AB/W31-E101"
    #test get_card_info
    #one_card = get_card_info(main_site_url, test_id)

    #print(one_card)
    cards = card_search()
    print(cards)
    save_cards(cards)
    # card = cards[0]
    # card = stats

    # print(cards)
    # main_path = os.path.normpath(os.getcwd() + os.sep + os.pardir + os.sep + "\card_viewer")
    # print(main_path)

    #img_link = main_site_url + card["Card Img"]

    # original save image to file
    #output = Image.open(requests.get(card_img_link, stream=True).raw)
    #output.save(card_id + ".png")

    # Troubleshooting downloading card images
    #for card in cards:
        #img_link = main_site_url + card["Card Img"]
        #try:
            #print("Connected to card database. Downloading cards...")
            #output = Image.open(requests.get(img_link, stream=True).raw)
            #output.save(card["Card No."] + ".png")
            #print("Saved card %s" % card["Card Name"])
        #except requests.exceptions.ConnectionError:
            #print("Reconnecting to website...")
            #time.sleep(5)

if __name__ == '__main__':
    main()