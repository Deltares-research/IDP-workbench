import solara

from solara_mekong.pages.home import Page as home_page
from solara_mekong.pages.hazard import Page as hazard_page
from solara_mekong.pages.impact import Page as impact_page

title = "Salinity Intrusion Dashboard for Mekong Delta"

routes = [
    solara.Route(path="/", component=home_page, label=title ),
    solara.Route(path="hazard", component=hazard_page, label=title ),
    solara.Route(path="impact", component=impact_page, label=title ),
]