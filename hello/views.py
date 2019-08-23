from datetime import date, timedelta
from django.shortcuts import render
from django.http import HttpResponse
import requests
from bs4 import BeautifulSoup
import re
from collections import OrderedDict


from .models import Greeting

DATE_MAP = {0: "maanantai", 1: "tiistai", 2: "keskiviikko", 3: "torstai", 4: "perjantai", 5: "lauantai", 6: "sunnuntai"}


def get_sodexo(location_id):
    t = date.today()
    month = t.month if t.month > 10 else ("0" + str(t.month))
    base_url = "https://www.sodexo.fi/ruokalistat/output/daily_json/" + location_id
    r = requests.get(f"{base_url}/{t.year}/{month}/{t.day}/fi")
    data = r.json()
    return [c["title_fi"] for c in data["courses"]]


def get_min():
    return get_sodexo("35005")


def get_hiili():
    return get_sodexo("131")


def crawl_factory():
    r = requests.get("https://ravintolafactory.com/lounasravintolat/ravintolat/helsinki-salmisaari/")

    soup = BeautifulSoup(r.text, "html.parser")

    today = DATE_MAP[date.weekday(date.today())].capitalize()
    h3 = soup.find("h3", string=re.compile(today))
    if not h3:
        return None

    next_p = h3.findNext("p")
    if next_p.find("img"):
        next_p = next_p.findNext("p")

    return [str(item).strip() for item in next_p.contents if str(item) != "<br/>"]


def crawl_garam_page(url):
    r = requests.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    wrapper = soup.find_all(class_="text-content")[2]
    if not wrapper or not wrapper.p or "VIIKKO" not in wrapper.p.text:
        return None

    today = DATE_MAP[date.weekday(date.today())].upper()
    tomorrow = DATE_MAP[date.weekday(date.today() + timedelta(1))].upper()

    all_p = wrapper.find_all("p")
    today_index = next(iter([i for i, s in enumerate(all_p) if today in s.text]), None)
    tomorrow_index = next(iter([i for i, s in enumerate(all_p) if tomorrow in s.text]), None)

    if not tomorrow_index:
        tomorrow_index = next(iter([i for i, s in enumerate(all_p) if "Hinnat" in s.text]), None)

    if today_index and tomorrow_index:
        return [p.text for p in all_p[today_index + 1: tomorrow_index]]

    return None


def crawl_oikeus():
    return crawl_garam_page("https://www.cafeteria.fi/ravintola-oikeus/")


def crawl_silta():
    return crawl_garam_page("https://www.cafeteria.fi/silta-itamerentalo/")

# Create your views here.
def index(request):
    data = OrderedDict(
        {
            "min": get_min(),
            "hiili": get_hiili(),
            "silta": crawl_silta(),
            "oikeus": crawl_oikeus(),
            "factory": crawl_factory(),
        }
    )
    return HttpResponse('Hello from Python!' + str(data))
    #return render(request, "index.html")


def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, "db.html", {"greetings": greetings})
