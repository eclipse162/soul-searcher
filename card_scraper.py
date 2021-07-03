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
                stats_dict[h.text] = d.next_element["src"].split("/")[-1].split(".")[0].capitalize()
        else:
            # strip newlines and carriage returns
            stats_dict[h.text] = d.text.replace("\n", "").replace("\r","")

    return stats_dict


def card_search():
    main_site = "https://en.ws-tcg.com"
    url = main_site + "/cardlist/cardsearch/exec"
    session = HTMLSession()
    res = session.get(url)
    soup = BeautifulSoup(res.content, "lxml")
    #driver = webdriver.Firefox()
    #driver.get(url)

    # find the card search forms
    initial_form = soup.find("form", class_="cardSearchForm")
    forms = soup.find("form", class_="cardSearchForm").table.find_all("td")
    # forms = soup.find("form", class_="cardSearchForm").table.find_all("tr")
    #print(forms)

    # create a dictionary of the required forms to fill out
    details = {}
    # form_names = ["All these words","Any of these words","None of these words","Target card name",
    #               "Target special attributes", "Target text", "Target card number",
    #               "Has Counter ability", "Has Clock ability", "Show simple list"]
    action = initial_form.attrs.get("action").lower()
    method = initial_form.attrs.get("method", "get").lower()
    inputs = []
    for input_tag in forms:
        if input_tag.input:
            in_type = input_tag.input["type"]
            in_name = input_tag.input["name"]
            in_value = input_tag.attrs.get("value","")
            inputs.append({"type": in_type, "name": in_name, "value": in_value})

        elif input_tag.span:
            #TODO: detect span attributes
            in_type = input_tag.span["class"]
            in_name = input_tag.span["name"]
            in_value = input_tag.span.attrs.get("value",0)
            inputs.append({"type": in_type, "name": in_name, "value": in_value})

        # elif input_tag.select:
        #     select_tags = set(input_tag.contents)
        #     if '\n' in select_tags:
        #         select_tags.remove('\n')
        #
        #     if "～\n" in select_tags:
        #         select_tags.remove("～\n")
        #
        #     for item in select_tags:
        #         in_name = item["name"]
        #         in_value = item.attrs.get("value","")
        #         options = []
        #         for op in item.find_all("option"):
        #             options.append((op["value"], op.text))
        #
        #         inputs.append({"name": in_name, "value": in_value, "option": options})

    details["action"] = action
    details["method"] = method
    details["inputs"] = inputs

    print(details)
    #
    # # create data to be submitted
    data = {}
    # counter = 0
    # for input_tag in details["inputs"]:
    #     if input_tag["type"] == "hidden":
    #         data[input_tag["name"]] = input_tag["value"]
    #     elif input_tag["type"] != "submit":
    #         value = input("Enter value for '%s' (input type: %s): " % (form_names[counter], input_tag["type"]))
    #         if value == "":
    #             if input_tag["type"] == "checkbox":
    #                 data[input_tag["name"]] = 1
    #             else:
    #                 data[input_tag["name"]] = input_tag["value"]
    #         else:
    #             data[input_tag["name"]] = value
    #         counter += 1
    #
    # #print(data)
    #
    # new_url = urljoin(url, details["action"])
    #
    # if details["method"] == "post":
    #     res = session.post(new_url, data=data)
    # elif details["method"] == "get":
    #     res = session.get(new_url, params=data)
    #
    # s = BeautifulSoup(res.content, "lxml")
    #
    # card_results = []
    # print("Compiling results...")
    #
    # # Display data based on simple search selection
    # if data["show_small"] == "0":
    #     # Simple search off
    #     search = s.find("div", id="searchResults").find("table", id="searchResult-table")
    #     card_links = search.find_all("th")
    #     for card in card_links:
    #         card_info = get_card_info(main_site, card.a["href"].split("=")[1])
    #         card_results.append(card_info)
    #
    # else:
    #     # Simple search on
    #     search = s.find("div", id="searchResults").find("table", id="searchResult-table-simple")
    #     card_rows = search.find_all("tr")[1:]     # skip the first table row because it is only labels
    #     for row in card_rows:
    #         card_info = get_card_info(main_site, row.td.text)
    #         card_results.append(card_info)
    #
    # print("Finished compilation.")
    #
    # # TODO: Return links for previous/next page in case of multiple pages
    # pages = s.find("p", class_="pageLink").find_all("a", rel=True)
    # #if pages.a["rel"]
    # return card_results


def main():
    # get site and URL of a card's stats
    # main site URL used later for getting image link
    main_site_url = "https://en.ws-tcg.com"
    url = "https://en.ws-tcg.com/cardlist/list/?cardno=FZ/S17-TE04"
    # TODO: add in support for Japanese site


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

    cards = card_search()

    #print(cards)

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