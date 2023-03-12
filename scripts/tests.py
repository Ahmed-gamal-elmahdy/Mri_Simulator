import json


seq = {"name":"simple",
    'Rf': {
    "x":[1,2,3,4],
    "y":[5,5,5,5]
},
'Gz': {
    "x":[1,2,3,4],
    "y":[5,5,5,5]
},
'Gy': {
    "x":[1,2,3,4],
    "y":[5,5,5,5]
},
'Gx': {
    "x":[1,2,3,4],
    "y":[5,5,5,5]
},
'Ro': {
    "x":[1,2,3,4],
    "y":[5,5,5,5]
},
}


jsonfile=json.dumps(seq)
print(json.loads(jsonfile)["Rf"]["y"])