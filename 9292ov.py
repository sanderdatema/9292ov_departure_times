"""
Written by Sander Datema (sanderdatema@gmail.com)

Table view based on MyTableView.py (https://github.com/tdamdouni/Pythonista)
9292 Data retrieval based on https://github.com/revspace/ovapi-flipdot

* Go to http://v0.ovapi.nl/stopareacode and find your StopAreaCode,
* Then go to http://v0.ovapi.nl/stopareacode/<your StopAreaCode> to see all the
  stops (TimingPointCode) that area has. Most of the time it'll be two stops,
  one for each side of the road.
* Under passes, you'll find all buses that will pass that stop in the near
  future. That means that it will be mostly when you check this late at night!
* Choose which bus lines (LinePublicNumber) you want to select
* Fill out everything under data below
* Sometimes bus line names are too long, you can replace certain words under
  destination_name_replacements
"""

import ui
from requests import get as request
from dateutil.parser import parse as parse_datetime
from datetime import datetime

# todo: add line direction
data = {
    "Station Nijmegen": {
        "StopAreaCode": "NmCS",
        "TimingPointCodes": ["60001002"],
        "LinePublicNumbers": ["10", "300", "6", "9", "SB58", "83"],
    },
    "Radboudumc": {
        "StopAreaCode": "nmgumc",
        "TimingPointCodes": ["60001281", "60001280"],
        "LinePublicNumbers": ["10", "300", "6", "9", "SB58", "83"],
    },
}

destination_name_replacements = [
  ["C S", "CS"],
  [" via Bemmel", ""],
]


def get_9292_data(station):
    selected_buses = []

    result = request(
        "http://kv78turbo.ovapi.nl/stopareacode/" + station["StopAreaCode"]
    ).json()

    for area in result:
        for bus_stop in result[area]:
            if bus_stop in station["TimingPointCodes"]:
                for planning in result[area][bus_stop]["Passes"]:
                    bus = result[area][bus_stop]["Passes"][planning]
                    if bus["LinePublicNumber"] in station["LinePublicNumbers"]:
                        depart_in_minutes = max(
                            0,
                            int(
                                (
                                    parse_datetime(bus["ExpectedDepartureTime"])
                                    - datetime.now()
                                ).total_seconds()
                                / 60
                            ),
                        )

                        destination_name = bus["DestinationName50"]
                        destination_name = destination_name.strip()
                        for replacement in destination_name_replacements:
                            destination_name = destination_name.replace(
                                replacement[0], replacement[1]
                            )

                        selected_bus = "%s (%s) - %sm" % (
                            bus["LinePublicNumber"],
                            destination_name,
                            depart_in_minutes,
                        )

                        selected_buses.append((depart_in_minutes, selected_bus))

    selected_buses.sort()
    return selected_buses


class TableView(ui.View):
    def __init__(self):
        self.list = list(data)

        self.tv = ui.TableView()
        self.tv.name = "Locatie"
        self.tv.delegate = self
        self.tv.data_source = self

        nv = ui.NavigationView(self.tv)
        nv.present("sheet")

    def tableview_did_select(self, tableview, section, row):
        tv = ui.TableView()
        tv.name = self.list[row]

        sub_ds = SubTableView(tv.name)
        tv.data_source = sub_ds
        tv.delegate = sub_ds
        tableview.navigation_view.push_view(tv)

    def tableview_number_of_sections(self, tableview):
        return 1

    def tableview_number_of_rows(self, tableview, section):
        return len(data)

    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.text_label.text = self.list[row]
        return cell


class SubTableView(object):
    def __init__(self, station):
        self.busses = get_9292_data(data[station])

        self.tv = ui.TableView()
        self.tv.delegate = self
        self.tv.data_source = self

    def tableview_number_of_sections(self, tableview):
        return 1

    def tableview_number_of_rows(self, tableview, section):
        return len(self.busses)

    def tableview_cell_for_row(self, tableview, section, row):
        cell = ui.TableViewCell()
        cell.text_label.text = self.busses[row][1]
        return cell

TableView()
