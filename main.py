import requests
import json

##################### Ipify ########################

def get_my_ip():
    return requests.get("https://api.ipify.org/?format=text").text.strip()

################### Digital Ocean ###################

class DomainRecords:
    def __init__(self, token, domain):
        self.__base_url = "https://api.digitalocean.com/v2/domains/%s/records" % domain
        self.__headers = { "Authorization": "Bearer " + token }

    def get_all(self):
        response_body = requests.get(self.__base_url, headers=self.__headers).json()
        return response_body["domain_records"]
    
    def update(self, id, data):
        requests.put(self.__base_url + "/" + str(id), data={ "data": data }, headers=self.__headers)
    
    def create(self, ttl, name, data):
        requests.post(self.__base_url, data={ "type": "A", "ttl": ttl, "name": name, "data": ip }, headers=self.__headers)

    def delete(self, id):
        requests.delete(self.__base_url + "/" + str(id), headers=self.__headers)

###################### Difference ###################

class Difference:
    def __init__(self, current_structures, maintained_identifiers, identify_structure_method, update_predicate):
        self.to_create_identifiers = maintained_identifiers[:]
        self.to_delete = []
        self.to_update = []
        self.to_do_nothing = []

        for item in current_structures:
            identifier = identify_structure_method(item)
            if identifier in maintained_identifiers:
                self.to_create_identifiers.remove(identifier)

                if update_predicate(item):
                    self.to_update.append(item)
                else:
                    self.to_do_nothing.append(item)
            else:
                self.to_delete.append(item)

##################### utilities #####################

def read_all_text(file):
    try:
        with open(file, "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

def write_all_text(file, text):
    with open(file, "w") as f:
        f.write(text)

def read_json(file):
    text = read_all_text(file);
    if text is None:
        return None
    return json.loads(text)

####################### main ########################

config = read_json("config.json")
if config is None:
    print("No configuration file!")
    exit(1)

last_ip = read_all_text(config["last_ip_file"])
my_ip = get_my_ip()

changed = last_ip != my_ip
print("IP address: %s (%s)" % (my_ip, ("changed" if changed else "unchanged")))
if not changed:
    exit()

write_all_text(config["last_ip_file"], my_ip)

api = DomainRecords(config["token"], config["domain"])

domain_records = api.get_all()
a_records = [r for r in domain_records if r["type"] == "A"]

difference = Difference(
    current_structures = a_records, 
    maintained_identifiers = config["managed_domains"], 
    identify_structure_method = lambda x: x["name"],
    update_predicate = lambda x: my_ip != x
)

for record in difference.to_do_nothing:
    print("OK: " + record["name"])

for record in difference.to_update:
    print("Update: " + record["name"])
    api.update(record["id"], my_ip)

for record in difference.to_delete:
    print("Delete: " + record["name"])
    api.delete(record["id"])

for name in difference.to_create_identifiers:
    print("Create: " + domain_name)
    api.create(config["ttl"], name, my_ip)
